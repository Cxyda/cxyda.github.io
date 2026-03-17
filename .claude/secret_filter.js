#!/usr/bin/env node

/**
 * Claude Request Filter with Gitleaks Integration
 *
 * Intercepts HTTP/HTTPS requests and scans them for credentials using gitleaks.
 * Redacts any found credentials before sending the request.
 *
 * Usage: NODE_OPTIONS=--require=./secret_filter.js claude
 */

const https = require('https');
const http = require('http');
const fs = require('fs');
const path = require('path');
const { execSync, spawnSync } = require('child_process');
const os = require('os');

// Configuration
const LOG_FILE = '/tmp/claude_secret_filter.log'
const GITLEAKS_VERSION = '8.28.0';

// abort if not running with full claude path
try {
    const claudePath = execSync('which claude', { encoding: 'utf8' }).trim();
    const commandLine = process.argv.join(' ');

    if (!commandLine.includes(claudePath)) {
        return
    }
} catch (error) {
    log(`⚠️  Could not determine claude path, filter will not run: ${error}`);
    return
}

// Get cache directory based on platform
function getCacheDir() {
    const platform = os.platform();
    const home = os.homedir();

    if (platform === 'darwin') {
        return path.join(home, 'Library', 'Caches', 'gitleaks');
    } else if (platform === 'win32') {
        return path.join(process.env.LOCALAPPDATA || path.join(home, 'AppData', 'Local'), 'gitleaks', 'cache');
    } else {
        // Linux/Unix - follow XDG Base Directory specification
        return path.join(process.env.XDG_CACHE_HOME || path.join(home, '.cache'), 'gitleaks');
    }
}

const CACHE_DIR = getCacheDir();
// Ensure cache directory exists
if (!fs.existsSync(CACHE_DIR)) {
    fs.mkdirSync(CACHE_DIR, { recursive: true });
}

// Map system architecture to gitleaks naming convention
function getGitleaksArch() {
    const platform = os.platform();
    const arch = os.arch();

    if (platform === 'linux') {
        if (arch === 'x64') return 'linux_x64';
        if (arch === 'arm64') return 'linux_arm64';
        if (arch === 'arm') return 'linux_armv7';
        if (arch === 'ia32') return 'linux_x32';
    } else if (platform === 'darwin') {
        if (arch === 'x64') return 'darwin_x64';
        if (arch === 'arm64') return 'darwin_arm64';
    }

    return null;
}

// Get gitleaks path
function getGitleaksPath() {
    // First check if gitleaks is available globally
    try {
        const globalPath = execSync('which gitleaks', { encoding: 'utf8', stdio: ['pipe', 'pipe', 'ignore'] }).trim();
        if (globalPath && fs.existsSync(globalPath)) {
            return globalPath;
        }
    } catch (e) {
        // Not available globally, fall through to cache directory
    }

    // Fall back to cache directory
    const arch = getGitleaksArch();
    if (!arch) return null;
    return path.join(CACHE_DIR, `gitleaks-${arch}`);
}

// Install gitleaks if not present (either globally not in the cached location)
function installGitleaks() {
    const arch = getGitleaksArch();
    if (!arch) {
        console.error('❌ Unsupported architecture:', os.platform(), os.arch());
        console.error('Please install gitleaks manually from: https://github.com/gitleaks/gitleaks/releases');
        return null;
    }

    const gitleaksPath = getGitleaksPath();

    // Check if already installed
    if (fs.existsSync(gitleaksPath)) {
        try {
            execSync(`${gitleaksPath} version`, { stdio: 'ignore' });
            return gitleaksPath;
        } catch (e) {
            // Exists but not executable, try to reinstall
        }
    }

    console.error(`🔧 Installing gitleaks for ${arch}...`);

    const downloadUrl = `https://github.com/gitleaks/gitleaks/releases/download/v${GITLEAKS_VERSION}/gitleaks_${GITLEAKS_VERSION}_${arch}.tar.gz`;
    const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'gitleaks-'));

    try {
        // Download and extract
        execSync(`curl -sL "${downloadUrl}" | tar -xz -C "${tempDir}" gitleaks`, {
            stdio: 'pipe'
        });

        // Move to cache directory for reuse across projects
        const tempGitleaks = path.join(tempDir, 'gitleaks');
        if (fs.existsSync(tempGitleaks)) {
            fs.renameSync(tempGitleaks, gitleaksPath);
            fs.chmodSync(gitleaksPath, 0o755);
            console.error(`✅ Gitleaks installed at ${gitleaksPath}`);
            return gitleaksPath;
        } else {
            console.error('❌ Failed to extract gitleaks');
            return null;
        }
    } catch (error) {
        console.error('❌ Failed to install gitleaks:', error.message);
        return null;
    } finally {
        // Cleanup temp dir
        try {
            fs.rmSync(tempDir, { recursive: true, force: true });
        } catch (e) {}
    }
}

// Initialize gitleaks
const GITLEAKS_PATH = installGitleaks();

if (!GITLEAKS_PATH) {
    console.error('⚠️  Filter running without gitleaks - credentials will NOT be detected');
    return
}

// Log function
function log(message) {
    const timestamp = new Date().toISOString();
    fs.appendFileSync(LOG_FILE, `${timestamp} ${message}\n`);
}

// Scan content with gitleaks and return findings + redacted version
function scanAndRedact(content) {
    if (!GITLEAKS_PATH || !content || content.length === 0) {
        return { redacted: content, detected: false };
    }

    try {
        const startTime = Date.now();

        // Always use verbose mode
        const verboseResult = spawnSync(GITLEAKS_PATH, [
            'stdin',
            '--no-banner',
            '--no-color',
            '-v'
        ], {
            input: content,
            encoding: 'utf8',
            maxBuffer: 50 * 1024 * 1024
        });

        const scanTime = Date.now() - startTime;
        const gitleaksOutput = verboseResult.stdout + verboseResult.stderr;

        // Always log the gitleaks result
        log(`GITLEAKS SCAN (${scanTime}ms):\n${gitleaksOutput}`);

        // Exit code 0 = no secrets, 1 = secrets found
        if (verboseResult.status === 0) {
            return { redacted: content, detected: false };
        }

        // Extract secrets from gitleaks output and redact them
        let redactedContent = content;
        const secretsFound = [];

        // Parse gitleaks output to find Secret: lines
        const secretPattern = /Secret:\s*(.+?)(?:\n|$)/g;
        let match;

        while ((match = secretPattern.exec(gitleaksOutput)) !== null) {
            const secret = match[1].trim();
            if (secret && secret.length > 0) {
                secretsFound.push(secret);
            }
        }

        // Redact each found secret
        if (secretsFound.length > 0) {
            for (const secret of secretsFound) {
                const replacement = 'X'.repeat(secret.length);
                // Use global replace to catch all occurrences
                redactedContent = redactedContent.split(secret).join(replacement);
            }

            return {
                redacted: redactedContent,
                detected: true,
                output: gitleaksOutput,
                cannotRedact: false
            };
        }

        // If we detected secrets but couldn't extract them, don't redact
        return {
            redacted: content,
            detected: true,
            output: gitleaksOutput,
            cannotRedact: true
        };

    } catch (error) {
        log(`Error scanning with gitleaks: ${error.message}`);
        return { redacted: content, detected: false };
    }
}

// Patch fetch if available
if (typeof globalThis.fetch === 'function') {
    const originalFetch = globalThis.fetch;

    globalThis.fetch = async function(url, options = {}) {
        const urlStr = typeof url === 'string' ? url : url.toString();

        // Check if there's a body to scan
        if (options.body) {
            let bodyStr = '';

            if (typeof options.body === 'string') {
                bodyStr = options.body;
            } else if (options.body instanceof Buffer) {
                bodyStr = options.body.toString('utf8');
            } else if (typeof options.body === 'object') {
                bodyStr = JSON.stringify(options.body);
            }

            if (bodyStr) {
                // Check if we should scan this URL
                if (shouldScanUrl(urlStr)) {
                    const result = scanAndRedact(bodyStr);

                    if (result.detected) {
                        log(`  ⚠️  CREDENTIALS DETECTED AND REDACTED`);
                        log(`  ${result.output}`);

                        if (!result.cannotRedact) {
                            // Replace body with redacted version
                            options = { ...options, body: result.redacted };
                        }
                    }
                }
            }
        } else {
            log(`Fetch to ${urlStr} (no body)`);
        }

        return originalFetch.call(this, url, options);
    };
}

// Store original methods
const originalHttpsRequest = https.request;
const originalHttpRequest = http.request;

// Helper to extract URL from request options
function extractUrl(options, protocol) {
    if (typeof options === 'string') {
        return options;
    } else if (options.href) {
        return options.href;
    } else {
        return `${protocol}://${options.hostname || options.host}${options.path || '/'}`;
    }
}

// Check if URL should be scanned with gitleaks
function shouldScanUrl(url) {
    return url.includes('https://api.anthropic.com/v1/messages');
}

// Unified request interceptor
function createRequestInterceptor(originalRequest, protocol) {
    return function(...args) {
        const options = args[0];
        const url = extractUrl(options, protocol);

        // Create the request
        const req = originalRequest.apply(this, args);

        // Intercept write and end to capture body
        const originalWrite = req.write;
        const originalEnd = req.end;
        let requestBody = [];

        req.write = function(chunk) {
            if (chunk) {
                requestBody.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
            }
            return originalWrite.apply(this, arguments);
        };

        req.end = function(chunk) {
            if (chunk) {
                requestBody.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
            }

            // Process the body
            if (requestBody.length > 0) {
                let body = Buffer.concat(requestBody);
                const originalSize = body.length;

                // Check if we should scan this URL
                if (shouldScanUrl(url)) {
                    // Scan and redact
                    const bodyStr = body.toString('utf8');
                    const result = scanAndRedact(bodyStr);

                    if (result.detected) {
                        log(`  ⚠️  CREDENTIALS DETECTED AND REDACTED`);
                        log(`  ${result.output}`);

                        if (result.cannotRedact) {
                            log(`  ⚠️  Could not parse gitleaks output, content passed through unchanged`);
                        }

                        // Replace the body with redacted version
                        body = Buffer.from(result.redacted, 'utf8');

                        // Write the redacted body
                        originalWrite.call(req, body);
                    } else {
                        // Write original body
                        originalWrite.call(req, body);
                    }
                } else {
                    // Write original body
                    originalWrite.call(req, body);
                }
            } else {
                log(`${protocol.toUpperCase()} Request to ${url} (no body)`);
            }

            // Call original end without chunk (we already wrote it if needed)
            const endArgs = Array.from(arguments);
            endArgs[0] = undefined; // Clear the chunk argument
            return originalEnd.apply(req, endArgs);
        };

        return req;
    };
}

// Patch https.request
https.request = createRequestInterceptor(originalHttpsRequest, 'https');

// Patch http.request
http.request = createRequestInterceptor(originalHttpRequest, 'http');

log('='.repeat(80));
log('Filter module loaded - scanning all HTTP/HTTPS/fetch requests for credentials');
log(`Gitleaks: ${GITLEAKS_PATH || 'NOT AVAILABLE'}`);

console.log('🔒 Claude secret filter active - scanning requests for credentials');