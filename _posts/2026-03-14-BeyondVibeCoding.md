---
layout: post
title: "Beyond Vibe-Coding: A Disciplined Workflow for AI-Assisted Software Development with Claude Code"
tags: [AI,Workflow,Claude Code]
---

*Originally published on the [InnoGames Technology Blog](https://blog.innogames.com/beyond-vibe-coding-a-disciplined-workflow-for-ai-assisted-software-development-with-claude-code/). Written in early March 2026, shortly after the release of Claude Opus 4.6.*

---

Over the past few weeks I've been refining a workflow for AI-assisted development that I think is worth sharing. I don't share it because any single project built with it is a masterpiece, but because the process challenges a lot of assumptions about what AI-assisted development actually looks like when done with discipline.

**This is not vibe-coding.** I want to make that distinction upfront.

If you've been following the discourse around AI-assisted development, you've probably encountered two terms gaining traction: **Spec-Driven Development (SDD)** and **Agentic Engineering**. SDD -- championed by GitHub with their open-source [Spec Kit](https://github.blog/ai-and-ml/generative-ai/spec-driven-development-with-ai-get-started-with-a-new-open-source-toolkit/) toolkit and explored in an [academic paper on arXiv](https://arxiv.org/abs/2602.00180) -- treats specifications as the source of truth and code as a generated artifact. The workflow is Specify, Plan, Task, Implement. Agentic Engineering -- a term coined by Andrej Karpathy (the same person who coined "vibe coding") and expanded on by Addy Osmani in his book [*Beyond Vibe Coding*](https://www.oreilly.com/library/view/beyond-vibe-coding/9798341634749/) -- describes the practice of orchestrating AI agents while acting as architect, reviewer, and decision-maker.

My workflow draws heavily from both of these ideas. The planning pipeline is essentially SDD: structured specifications drive every implementation step. The execution model is agentic engineering: I orchestrate AI agents through composable skill commands rather than writing code myself. Where my approach diverges is in the emphasis on **automated quality gates** as first-class workflow steps -- not just planning rigor on the front end, but continuous automated verification throughout. I've been calling this aspect "gate-coding" internally: the developer defines goals, the AI plans, the developer reviews, and the AI executes -- with quality gates at every stage.

Think of the AI as the car, not the passenger. The developer doesn't do the traveling -- the car does. The developer doesn't need to understand the combustion engine, the transmission, or the fuel injection system. What the developer does is choose the destination, pick the route, and steer. The quality gate is simple: did we arrive safely, comfortably, and without crashing into anything along the way?

You don't micromanage a car. You don't manually fire each spark plug. But you also don't close your eyes and take your hands off the wheel. You watch the road, you correct course when the GPS suggests a questionable turn, and you brake when something doesn't look right. Eyes on the road, hands on the wheel, but the engine does the work.

It is NOT a fully agentic, auto-pilot-ON workflow (yet) where you hand off control and let the AI get your work done mindlessly.

What this approach does enable is something that sounds extreme but has become my daily reality: **in most cases even 100% AI-written code on large, live production projects** -- without sacrificing code quality, architectural integrity, or your own sanity. Not on toy projects or weekend prototypes, but on professional production codebases -- I'm actively using this workflow on a live multi-platform game with 1+ million lines of code (including generated code), strict layered architectures, comprehensive test suites, and real users. The key insight is that "AI-written" doesn't mean "unsupervised." Every line passes through quality gates, every feature starts from a reviewed plan, and the developer stays in full control of *what* gets built and *how*. The AI just does the typing.

---

## The Workflow

My workflow is built around custom **Claude Code skills** -- reusable, prompt-encoded commands that chain together into a pipeline. I rarely type freeform prompts anymore. Instead, I invoke skills that encode my workflow expectations, quality standards, and architectural constraints.

### What Are Claude Code Skills?

Claude Code supports user-defined "skills": markdown files that act as structured prompt templates invoked via slash commands. Each skill encodes a specific workflow step -- what context to gather, what actions to take, what quality standards to enforce, and what artifacts to produce. They're not plugins or compiled code; they're prompt engineering distilled into reusable, composable building blocks.

This matters because it turns tribal knowledge, team conventions, and hard-won lessons into repeatable automation. Instead of remembering to "always check for compile errors after implementation" or "always reference the ADR files before planning," the skill does it automatically, every time.

### The Pipeline

Here's the core pipeline I use for feature development:

```
/plan-high-level [goals]
/plan-detailed [path to high-level plan]
/plan-debate [path to plan file]    // (optional)
/implement-fe [path to plan file]
OR
/implement-phase [phase number] [path to plan doc]
```

For a full production workflow with Jira integration, it extends to:

```
/add-issue [ticket-number]
/research-code
/plan-high-level                    // (optional)
/plan-detailed                      // (optional)
/implement-phase
/openpr
/finish-task
```

**I type only the commands -- no prompts.** Each command handles its own context gathering, execution, and validation. But between these developer-invoked commands, a layer of automated quality gates runs silently -- spawned by the skills themselves as forked sub-agents. The developer never calls them directly; they fire automatically at each transition point:

```
/research-code
  |-- ad-quality-gate <-- validates research thoroughness
/plan-high-level
  |-- ad-quality-gate <-- validates architectural coverage
  |-- pre-implementation-quality-gate <-- validates plan is grounded in reality
/implement-phase
  |-- unity-quality-gate <-- compilation, tests, play mode
  |-- review <-- code quality and architecture
  |-- post-phase-implementation-quality-gate <-- validates all deliverables present
  |-- scope-drift-quality-gate <-- detects out-of-scope changes
/openpr
  |-- pre-pr-quality-gate <-- test coverage and leftover markers (non-blocking)
```

If any blocking gate fails, the calling skill loops back to fix the issue and re-runs the gate -- the developer doesn't need to intervene unless the problem can't be auto-resolved. Let me describe what each skill does and why it exists.

### Skill Breakdown

**`add-issue`** -- Bootstraps a new task. It pulls the Jira ticket (title, description, acceptance criteria, attachments, screenshots), creates a local issue folder with structured context files, creates a git branch following naming conventions, and transitions the ticket to "In Progress." The purpose: eliminate the manual overhead of task setup and ensure Claude always starts with the full picture of what needs to be done.

**`research-code`** -- Analyzes the existing codebase for everything relevant to the task. It reads project documentation, Architecture Decision Records (ADRs), traces through relevant service interfaces, and documents its findings in a structured research file. The purpose: build a shared understanding of the current state before anyone starts planning changes. This prevents Claude from proposing solutions that conflict with existing architecture.

**`plan-high-level`** -- Takes goals (either from a Jira ticket or a goals document) and produces a structured architectural plan. This includes architecture diagrams, file creation/modification tables for each layer, phase dependency graphs, and explicit scope boundaries. It respects existing ADRs and design principles. The purpose: catch architectural mistakes before they become code. This is the "think before you build" step. I review this closely, push back on things I disagree with, and iterate.

**`plan-debate`** -- An adversarial planning skill that stress-tests a high-level plan before moving to detailed planning. It spawns two AI sub-agents -- a Planner and a Challenger -- that debate the plan over up to 5 rounds. The Challenger critiques assumptions, finds gaps, and raises edge cases; the Planner revises and defends. The output is a battle-tested plan where unresolved disagreements are explicitly documented as trade-offs. The purpose: catch architectural blind spots that a single AI (or a single developer) would miss. I describe the mechanics in detail further below.

**`plan-detailed`** -- Breaks each phase from the high-level plan into a separate document with pseudo-code, edge cases, test specifications, and step-by-step implementation instructions. Each step has explicit acceptance criteria. The purpose: give the implementation agent unambiguous instructions that leave minimal room for interpretation or scope creep.

**`fix`** -- A dedicated bug-fixing skill. Given a ticket ID or bug description, it investigates the issue by tracing all relevant execution paths, identifies the root cause (never just patching symptoms), implements the fix, verifies it with code review, and creates a regression test. The purpose: turn bug reports into verified fixes with a single command. It's particularly effective because it forces a root-cause-first approach -- Claude can't just slap a null check on the symptom and call it done.

**`implement-fe`** -- The core implementation skill. It uses a specialized Unity developer agent that reads the plan, implements the code, and then runs quality-gate checks: compilation verification, test execution, and (via UnityMCP) Play-mode validation to catch runtime errors. It doesn't call a task "done" until the quality gate passes. The purpose: automate the full implement-verify loop so that implementation output is always in a working state.

**`implement-phase`** -- A scoped variant of `implement-fe` that implements exactly one phase from a multi-phase plan. Created specifically to prevent scope overreach -- Claude sometimes starts implementing Phase 3 when you asked for Phase 1. This skill makes the boundary explicit. The purpose: enforce scope discipline in large implementations.

**`unity-quality-gate`** -- Runs a full Unity validation loop: verify zero compilation errors and warnings, run all EditMode tests, enter Play mode and verify no runtime exceptions, stop Play mode and verify clean shutdown. If anything fails, it fixes the issue and loops until all checks pass. The purpose: automate the "does it actually work?" verification that developers do manually. This skill emerged organically from debugging sessions where I'd tell Claude to "press Play and fix all exceptions" -- it worked so well I formalized it. Invoked automatically by `implement-fe` and `implement-phase`.

**`review`** -- An automated code review skill that runs after implementation, before opening a PR. It reviews all changed code for quality, style, correctness, and adherence to project conventions. It checks for things like unnecessary complexity, missing test coverage, naming violations, and architectural rule breaches. The purpose: catch issues that the quality gate (which focuses on "does it compile and run?") doesn't cover -- the kind of feedback an expert developer would give in a pull request review. This adds another quality gate layer: the code doesn't just have to *work*, it has to be *good*. Invoked automatically by `implement-fe` and `implement-phase`.

The following quality gate skills are **never invoked by the developer directly**. They are called automatically by other skills as forked sub-agents -- isolated, read-only checks that run in their own context, produce a structured pass/fail verdict, and never modify files. They are the automated enforcement layer that makes the "gate-coding" aspect of this workflow real.

**`ad-quality-gate`** (Architectural Decisions Quality Gate) -- Validates that research findings and plans are architecturally thorough. It checks whether relevant ADRs and architecture docs were actually consulted during research, whether all affected architectural layers are covered (domain, application, presentation, infrastructure, configuration), whether key interfaces and integration points are identified, and whether the research depth matches the task complexity. For plans, it additionally cross-references the plan's file lists against the research -- flagging when the plan modifies a file that was never examined during research, or creates files in a directory that was never explored. Invoked automatically by `research-code` (after writing findings) and `plan-high-level` (after writing the plan). If it returns FAILED, the calling skill loops back to address the gaps and re-runs the gate.

**`pre-implementation-quality-gate`** -- Validates that an implementation plan is grounded in reality before implementation begins. It verifies that every file listed for modification actually exists, that parent directories for files to be created exist, that referenced interfaces and API signatures match the real codebase (catching hallucinated or stale APIs), that dependencies and packages are actually installed, that the plan doesn't violate any ADR rules, and that the plan is internally consistent (no phases referencing unlisted files). This gate closes the gap where a plan *reads* plausibly but references things that don't exist. Invoked automatically by `plan-high-level` (in parallel with the AD quality gate). If it returns FAILED, the plan must be revised and the gate re-run -- implementation cannot begin.

**`post-phase-implementation-quality-gate`** -- Validates that a completed implementation phase actually delivered everything the plan promised. It compares the plan's file creation and modification lists against actual git changes, verifies that interfaces and contracts match what downstream phases expect to consume, checks that explicit acceptance criteria are met (not just "compiles" but "did it create the 3 services listed?"), and scans the next phase to confirm its dependencies are satisfied. This gate catches the "silently drops features" problem -- where a phase compiles and runs but quietly omitted half its deliverables. Invoked automatically by `implement-phase` after each phase completes. If it returns FAILED, the missing deliverables must be created before the next phase can begin.

**`scope-drift-quality-gate`** -- Detects scope overreach after implementation. It diffs all actual code changes against the plan's authorized scope: flagging files modified that weren't in the plan, files created that weren't planned, unplanned renames or moves, surprise dependency additions, semantic drift within in-scope files (variable renames, code reformatting, extracted methods the plan didn't call for), and unplanned deletions. The plan defines what files may be touched; anything outside the plan is drift until proven otherwise. Invoked automatically by `implement-fe` and `implement-phase` after the unity quality gate and code review pass. If it returns FAILED, all out-of-scope changes must be reverted before proceeding.

**`pre-pr-quality-gate`** -- A fast, informative check before opening a PR. It verifies that test specifications from the detailed plan have corresponding tests that actually exist, checks the test coverage delta for new code (are new production files accompanied by test files?), and scans all changed lines for leftover development markers (`TODO`, `HACK`, `FIXME`, `TEMP`). Unlike the other gates, this one is **non-blocking** -- it reports findings but never prevents the PR from being opened. Invoked automatically by `openpr` as a background check; results are included in the final PR report.

**`openpr`** -- Pushes all changes, creates a pull request (with proper formatting and meaningful change descriptions), posts a notification to Slack, merges latest main branch (auto-resolving conflicts in generated files), and triggers CI. The purpose: eliminate the PR creation ceremony and ensure nothing is forgotten.

**`finish-task`** -- Compares what was actually implemented against the original plan, documents any deviations, updates project documentation if the changes warrant it, attaches a summary to the Jira ticket, closes all associated tickets, and cleans up the branch. The purpose: close the feedback loop between planning and implementation, and keep both project management artifacts and documentation in sync with reality.

### Adversarial Planning: The Planner/Challenger Debate

One of the most impactful workflow additions came from a simple observation: a single AI producing a plan tends to be overconfident. It proposes an approach and commits to it without seriously questioning its own assumptions. To address this, I built an adversarial planning skill called **`plan-debate`** that pits two AI agents against each other in a structured debate.

The architecture is straightforward. An orchestrator skill spawns two sub-agents via Claude Code's Task system: a **Planner** that proposes and a **Challenger** that critiques. They alternate turns in a strict protocol:

```
Round 1:  Planner PROPOSES   ->  Challenger CRITIQUES
Round 2:  Planner REVISES    ->  Challenger RE-EVALUATES
Round 3+: Planner REFINES    ->  Challenger NARROWS
Round 5:  Planner FINALIZES  ->  Challenger SIGNS OFF (or dissents)
```

Each round narrows the scope of disagreement. The Planner outputs a versioned plan with a decision table, noting which decisions are new, revised, or unchanged, plus sections for what it adopted from the Challenger and what it defended against. The Challenger responds with a verdict (CHALLENGE, ACCEPT-WITH-NOTES, or CONSENSUS), a decision scorecard, and ranked objections by severity. Critically, the Challenger must always state its **strongest remaining objection** -- the hill it's willing to die on.

Consensus detection is structural, not vibes-based. If the Challenger's verdict is CONSENSUS, the debate stops. If all remaining objections are moderate or lower, one final round addresses the notes. Round 5 is the safety net -- any unresolved disagreements become a "Trade-offs & Risks" section in the output, so you see exactly what wasn't agreed on.

To prevent token explosion across 10 potential agent invocations, each agent only receives the research summary, the latest plan version, and the latest critique -- not the full debate history. The "Resolved" and "Adopted" sections carry forward what matters without replaying every round.

The result: plans that have already survived adversarial scrutiny before you even read them. The downside is time -- a high-level plan that previously took 5-10 minutes now takes 20+ minutes. This looks and especially feels like a lot. But the quality improvement is substantial, and the plans hold up far better during implementation. The time is not lost -- the cost of spotting and addressing these gaps later would have been much higher.

---

## How Planning Works in Practice

Let me walk through the artifact flow this produces.

**Step 1:** I write a goals document describing what I want. For a typical feature -- say, expanding gameplay with new mechanics, combat changes, and economy updates -- this might be a 50-100 line markdown file (for very big changes) laying out design intent and constraints. Normally this is less than 20 lines of markdown.

**Step 2:** `/plan-high-level` expands these goals into a 200-500 line architectural overview with an architecture diagram, file creation tables for every layer, files to modify, and a phase dependency graph. It respects existing ADRs and design principles. I review this closely, push back on things I disagree with, and iterate.

**Step 3:** `/plan-detailed` breaks each phase into a separate document with full pseudo-code, edge cases, test specifications, and step-by-step implementation instructions. Each step has explicit acceptance criteria.

**Step 4:** I review the detailed plans carefully. Claude presents pseudo-code and edge cases it has identified. I try to find more, think about potential problems with the suggested solutions, and make manual edits to the plan documents before implementation begins.

**Step 5:** I clear the context window and use `/implement-fe` or `/implement-phase` on one phase at a time (two at most), then clear the context again for the next phase. This is critical -- context rot is real and dangerous.

```
Goals doc (~10 - ~20 lines)
  -> High-level plan (~200 lines)
    -> Detailed phase plan (500 - ~1000 lines)
      -> Implementation (one or two phases per session)
```

---

## Context Management is Everything

> **This is perhaps the most important lesson from the entire workflow.**

Context rot is a real phenomenon in LLM-based development. As the context window fills up with accumulated conversation history, tool outputs, and code snippets, the model's ability to stay focused degrades. It starts hallucinating issues that don't exist, initiating unrequested refactorings, or losing track of what it was actually asked to do. This is not a theoretical concern -- it happens reliably and predictably once the context gets crowded enough.

This is also why I exclusively use Opus for all implementation work. Sonnet is faster and cheaper, but it hallucates more often and overshoots scope far more aggressively -- which means more rework, more wasted time, and more risk of subtle bugs slipping through. The cost difference pays for itself many times over.

My rule of thumb: **clear the context after each workflow step**, and always clear it when the context window is more than 50% full. I start a fresh session for each task, referencing plan and outcome documents from previous steps to give Claude precise context quickly. The discipline is: **one phase per session, clear context between phases**, always reference the plan document so Claude knows exactly what it should be doing and -- just as importantly -- what it should NOT be doing.

The difference between these two approaches is night and day. Without discipline -- when you think "it'll probably be fine" and hand over vague, oversized tasks -- the result is pure chaos. Multiple agents going rogue, unrequested refactorings, hallucinated problems, and you scrambling to undo the damage.

With discipline -- clear plans, scoped sessions, quality gates -- the same AI becomes a highly effective team of focused workers, each doing exactly what was asked, while you calmly oversee the output.

---

## Architecture Decisions That Make AI Development Work

Some architectural choices turned out to be unexpectedly important for AI-assisted development:

**SOLID principles, especially Single Responsibility.** Small, focused files with clear responsibilities let Claude follow execution paths without its context getting overloaded. When a bug occurs, I can describe the behavior and Claude reliably traces through the service interfaces to find the root cause. With monolithic classes, it gets distracted by things it *thinks* could be the problem.

**Interfaces everywhere.** Every service behind an interface means Claude can reason about contracts without reading implementations. It also means tests use clean fakes, and dependency injection makes everything swappable.

**Text-based UI formats.** If your UI system uses text-based formats (like Unity's UI Toolkit with UXML/USS files, or web frameworks with HTML/CSS), the AI can read, write, and modify layouts and styles directly -- no clicking through visual editors. This is a massive enabler for AI-driven development.

**Architecture Decision Records (ADRs).** Short markdown documents recording what was decided and why (e.g., "All new controllers must be plain C# classes, not MonoBehaviours, to improve testability and ensure pause-safety"). These give Claude an amazing context source it can quickly look up and understand. They also build a living technical companion document for you as a developer. Crucially, they prevent Claude from "improving" decisions that were made deliberately.

**Data-driven design.** All balance values and configuration live in data assets, never hardcoded. The AI can create and configure data assets without manual editor work.

**Module boundaries enforced by the build system.** Whether it's assembly definitions in Unity, package boundaries in a monorepo, or module systems in other frameworks -- explicit boundaries prevent the AI from accidentally introducing circular dependencies or layer violations.

---

## Where Things Go Wrong

This workflow is not without friction. Here are the real pain points.

**Scope overreach.** Claude sometimes goes beyond what you explicitly ask for or dismisses your feedback. It might refactor surrounding code while fixing a bug, or start implementing Phase 3 when you asked for Phase 1 only. Opus does this far less than Sonnet. You can suppress this with explicit scope statements in prompts, but that means boilerplate. The `/implement-phase` skill was created specifically to address this.

**Plan mode escape.** When Claude is in planning mode, at the end it asks to exit Plan mode to write the final document. Sometimes it skips even that step and immediately starts implementing without asking -- which with my workflow is almost never what I want. This is the danger zone where Claude goes full YOLO.

**Need to keep Claude focused.** If you take shortcuts or think "it'll probably be fine," Claude can go off the rails really fast. The discipline of clearing context, referencing specific plan documents, and reviewing output at every gate is non-negotiable.

**Missing features without explanation.** Claude sometimes silently drops features from the implementation. No error, no mention -- it just doesn't do them. Review of implementation output against the plan catches it, and it's straightforward to add back, but it's a reminder that you must verify completeness.

**Skipping planning depth.** A hard lesson: even when detailed phase plans look solid on paper, they can have major gaps in implementation guidance. The root cause is often jumping too quickly from a short, vague high-level overview directly to detailed plans. The high-level plan needs to be stress-tested first. The adversarial Planner/Challenger debate was born directly from this failure. It adds significant time to the planning step, but the plans survive implementation far better.

---

## Reflections on Dependence

After working this way for several weeks, I can feel how dependent I'm becoming on internet connectivity and AI service availability.

When I hit service outages, my reaction was "let's take a break and continue when the service is back" rather than switching to manual development. Even though I could still do it all by hand, I didn't want to. That's genuinely a bit unsettling, and something I need to be intentional about. Keeping your hands-on craft sharp is important -- not just as a fallback, but as a way to stay effective at reviewing what the AI produces.

---

## Key Takeaways

Looking back at what makes this workflow effective:

1. **Structured planning before implementation.** Never let Claude start coding from a vague description. The plan-review-implement pipeline catches architectural mistakes before they become code. A useful mental model: AI is like a team of junior developers with amazing workforce capabilities -- they can write code faster than any human team. But they likely don't understand the full problem, don't see the big picture, and tend to jump to conclusions too quickly. It is *your* job as the managing developer to think things through and to guide and challenge them: "Did you think about X?", "What about edge case Y?", "How does this interact with Z?" If you wouldn't hand a vague brief to a team of juniors and expect a perfect result, don't hand it to AI either.

2. **Strict context management.** One phase per session. Clear context between tasks. Reference specific plan files instead of relying on conversation history.

3. **Quality gates at every step.** This is where the workflow goes beyond what most SDD literature describes. Six automated quality gates run as forked sub-agents at every pipeline transition: research thoroughness validation, plan-vs-reality grounding checks, compilation/test/runtime verification, deliverable completeness checks, scope drift detection, and pre-PR regression scans. Most of these are invisible to the developer -- they fire automatically, and the calling skill loops to fix failures before proceeding. Claude doesn't call a task "done" until every gate passes. Most spec-driven approaches focus on planning rigor; automated verification throughout the entire pipeline closes the loop and catches the problems that even good plans miss.

4. **Architecture that supports AI.** SOLID principles, interfaces, small files, text-based UI, data-driven design, enforced module boundaries -- all of these make it easier for AI to navigate, understand, and modify the codebase reliably.

5. **ADRs as living context.** Architecture Decision Records are short, precise, and instantly useful for Claude to understand why things are the way they are. They prevent Claude from "improving" decisions that were made deliberately.

6. **Opus over Sonnet for implementation.** The reduced hallucination rate and better scope discipline justify the higher cost many times over. Sonnet's speed advantage doesn't matter when you have to redo work because it went off-script.

7. **Encode your workflow into skills.** Every time you find yourself repeating the same instructions, writing the same boilerplate prompts, or catching the same mistakes -- that's a signal to create a skill. Skills turn hard-won lessons into automated guardrails. They compound over time: each new skill makes the entire pipeline more reliable.

---

## Getting Started

If you want to try this approach, here's how to start small:

- **Start with planning skills.** Even just a `/plan` skill that forces Claude to produce a structured plan before writing code will dramatically improve output quality.
- **Add a quality gate.** A simple skill that runs your test suite and checks for compiler errors after implementation closes the most dangerous feedback gap.
- **Keep a CLAUDE.md file.** This is Claude Code's project-level instruction file. Put your coding conventions, architectural constraints, and "never do X" rules here. Claude reads it automatically at the start of every session.
- **Write ADRs.** Even two or three short decision records give Claude significantly better context than none. Start with the decisions that would be most expensive to violate.
- **Clear context aggressively.** When in doubt, start a new session. A fresh context with a good plan file beats a stale context with accumulated confusion every time.

The skills described in this post are custom-built for my workflow, but the patterns behind them are universal. You can build your own versions tailored to your stack, your conventions, and your team's workflow.
