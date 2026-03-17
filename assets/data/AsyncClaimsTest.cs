// AsyncClaimsTest.cs — Drop on any GameObject to verify blog post claims.
// Requires: UniTask (Cysharp.Threading.Tasks) and Unity 2023.1+ for Awaitable tests.
// Each test logs a [CLAIM #N] header so you can match results to blog sections.
// Tests run sequentially via coroutine to keep output readable.

using System;
using System.Collections;
using System.Threading;
using System.Threading.Tasks;
using Cysharp.Threading.Tasks;
using UnityEngine;

public class AsyncClaimsTest : MonoBehaviour
{
    // ──────────────────────────────────────────────
    // Master runner — kicks off all tests in order
    // ──────────────────────────────────────────────
    private IEnumerator Start()
    {
        Debug.Log("═══════════════════════════════════════════════════════");
        Debug.Log("  ASYNC CLAIMS VERIFICATION — Starting all tests");
        Debug.Log("═══════════════════════════════════════════════════════");

        // --- Section 1: Coroutines ---
        yield return StartCoroutine(Test01_CoroutineUnhandledException());
        yield return new WaitForSeconds(0.5f);

        yield return StartCoroutine(Test02_CoroutineTryCatchAroundNonYield());
        yield return new WaitForSeconds(0.5f);

        // --- Section 2: async void ---
        Test03_AsyncVoidUnhandledException();
        yield return new WaitForSeconds(1f);

        Test04_AsyncVoidTryCatchInside();
        yield return new WaitForSeconds(1f);

        Test05_AsyncVoidCallerCannotCatch();
        yield return new WaitForSeconds(1f);

        // --- Section 2: SynchronizationContext ---
        Test06_SyncContextCapturedOnMainThread();
        yield return new WaitForSeconds(2f);

        Test07_ConfigureAwaitFalseLeavesMainThread();
        yield return new WaitForSeconds(2f);

        Test08_TaskRunNoSyncContext();
        yield return new WaitForSeconds(2f);

        Test09_AfterAwaitTaskRunBackOnMainThread();
        yield return new WaitForSeconds(2f);

        // --- Section 3: Awaitable ---
        Test10_AwaitableThreadSwitching();
        yield return new WaitForSeconds(2f);

        // --- Section 4: UniTask ---
        Test11_UniTaskVoidForgetLogsException();
        yield return new WaitForSeconds(1f);

        Test12_UniTaskSuppressCancellationThrow();
        yield return new WaitForSeconds(1f);

        Test13_UniTaskGetCancellationTokenOnDestroy();
        yield return new WaitForSeconds(1f);

        // --- Section 2: destroyCancellationToken ---
        Test14_DestroyCancellationToken();
        yield return new WaitForSeconds(2f);

        // --- Bonus: async void exception propagation nuance ---
        Test15_AsyncVoidExceptionAfterAwait();
        yield return new WaitForSeconds(1f);

        Test16_AsyncVoidExceptionBeforeAwait();
        yield return new WaitForSeconds(1f);

        Debug.Log("═══════════════════════════════════════════════════════");
        Debug.Log("  ALL TESTS COMPLETE — Review logs above");
        Debug.Log("═══════════════════════════════════════════════════════");
    }

    // ══════════════════════════════════════════════════════════════════
    // TEST 01 — Coroutine: Unhandled exception stops coroutine, logs error
    // Blog claim (§1.3): "Unhandled exceptions in a coroutine are logged
    //   to the console (not silent) but stop the coroutine"
    // ══════════════════════════════════════════════════════════════════
    private IEnumerator Test01_CoroutineUnhandledException()
    {
        Debug.Log("───────────────────────────────────────────────────────");
        Debug.Log("[CLAIM 01] Coroutine: unhandled exception is logged and stops coroutine");
        Debug.Log("  Blog §1.3: 'Unhandled exceptions are logged to the console (not silent) but stop the coroutine'");
        Debug.Log("  EXPECT: An error logged by Unity, then 'SHOULD NOT APPEAR' should NOT appear.");

        yield return StartCoroutine(CoroutineThatThrows());

        Debug.Log("[CLAIM 01] If you see an error above BUT no 'SHOULD NOT APPEAR', claim is VERIFIED.");
    }

    private IEnumerator CoroutineThatThrows()
    {
        Debug.Log("  [inner] About to throw...");
        throw new Exception("Test01: Intentional coroutine exception");
        // ReSharper disable once HeuristicUnreachableCode
#pragma warning disable CS0162
        Debug.Log("  [inner] SHOULD NOT APPEAR — coroutine should have stopped");
        yield break;
#pragma warning restore CS0162
    }

    // ══════════════════════════════════════════════════════════════════
    // TEST 02 — Coroutine: try/catch works around non-yield code
    // Blog claim (§1.3): "you CAN use try/catch around normal
    //   (non-yield) statements in a coroutine"
    // ══════════════════════════════════════════════════════════════════
    private IEnumerator Test02_CoroutineTryCatchAroundNonYield()
    {
        Debug.Log("───────────────────────────────────────────────────────");
        Debug.Log("[CLAIM 02] Coroutine: try/catch works around non-yield statements");
        Debug.Log("  Blog §1.3: 'you CAN use try/catch around normal (non-yield) statements'");
        Debug.Log("  EXPECT: 'Caught!' message below.");

        bool caught = false;
        try
        {
            throw new Exception("Test02: Intentional exception in non-yield code");
        }
        catch (Exception e)
        {
            caught = true;
            Debug.Log($"  Caught! Exception message: {e.Message}");
        }

        Debug.Log($"[CLAIM 02] caught={caught}. If true, claim is VERIFIED.");
        yield return null;
    }

    // ══════════════════════════════════════════════════════════════════
    // TEST 03 — async void: Unhandled exception behavior
    // Blog claim (§2.6): "async void creates unobservable exceptions"
    //   and "Exception crashes the application!"
    // What actually happens in Unity: posted to UnitySynchronizationContext,
    //   logged as error. Does NOT crash.
    // ══════════════════════════════════════════════════════════════════
    private async void Test03_AsyncVoidUnhandledException()
    {
        Debug.Log("───────────────────────────────────────────────────────");
        Debug.Log("[CLAIM 03] async void: unhandled exception behavior");
        Debug.Log("  Blog §2.6: 'Exception crashes the application!'");
        Debug.Log("  EXPECT: Error logged by Unity. App should NOT crash (Unity catches via SyncContext).");
        Debug.Log("  NOTE: If the app does NOT crash, the blog's 'crashes the application!' wording is INACCURATE.");

        await Task.Yield(); // ensure we go through the async machinery
        throw new Exception("Test03: Intentional async void unhandled exception");
    }

    // ══════════════════════════════════════════════════════════════════
    // TEST 04 — async void: try/catch INSIDE works
    // Blog claim (§2.6 mitigation): "Always wrap in try/catch"
    // ══════════════════════════════════════════════════════════════════
    private async void Test04_AsyncVoidTryCatchInside()
    {
        Debug.Log("───────────────────────────────────────────────────────");
        Debug.Log("[CLAIM 04] async void: try/catch inside the method catches exceptions");
        Debug.Log("  Blog §2.6: Mitigation is to wrap in try/catch");
        Debug.Log("  EXPECT: 'Caught!' below, no unhandled error.");

        try
        {
            await Task.Yield();
            throw new Exception("Test04: Intentional exception inside try/catch");
        }
        catch (Exception e)
        {
            Debug.Log($"  Caught! Exception message: {e.Message}");
            Debug.Log("[CLAIM 04] VERIFIED — try/catch inside async void works.");
        }
    }

    // ══════════════════════════════════════════════════════════════════
    // TEST 05 — async void: Caller CANNOT catch exceptions
    // Blog claim (§2.6): "Cannot be caught by caller"
    // ══════════════════════════════════════════════════════════════════
    private void Test05_AsyncVoidCallerCannotCatch()
    {
        Debug.Log("───────────────────────────────────────────────────────");
        Debug.Log("[CLAIM 05] async void: caller's try/catch cannot catch the exception");
        Debug.Log("  Blog §2.6: 'Cannot be caught by caller'");
        Debug.Log("  EXPECT: Caller catch block does NOT fire. Error appears from SyncContext instead.");

        try
        {
            AsyncVoidThatThrows();
            Debug.Log("  Caller: returned from async void call (no exception caught here).");
        }
        catch (Exception e)
        {
            // This should NOT be reached for exceptions that happen after an await
            Debug.Log($"  Caller CAUGHT: {e.Message} — this would DISPROVE the claim!");
        }

        Debug.Log("[CLAIM 05] If caller did NOT catch and error appears separately, claim is VERIFIED.");
    }

    private async void AsyncVoidThatThrows()
    {
        await Task.Yield(); // forces true async execution
        throw new Exception("Test05: async void exception — caller should NOT catch this");
    }

    // ══════════════════════════════════════════════════════════════════
    // TEST 06 — SynchronizationContext: continuation on main thread
    // Blog claim (§2.2): UnitySynchronizationContext ensures
    //   continuations run on the main thread after await
    // ══════════════════════════════════════════════════════════════════
    private async void Test06_SyncContextCapturedOnMainThread()
    {
        Debug.Log("───────────────────────────────────────────────────────");
        Debug.Log("[CLAIM 06] SynchronizationContext: after await Task.Delay, back on main thread");
        Debug.Log("  Blog §2.2: 'UnitySynchronizationContext ensures continuations run on main thread'");

        int mainThreadId = Thread.CurrentThread.ManagedThreadId;
        Debug.Log($"  Before await — Thread ID: {mainThreadId}");

        await Task.Delay(500);

        int afterThreadId = Thread.CurrentThread.ManagedThreadId;
        Debug.Log($"  After await  — Thread ID: {afterThreadId}");

        bool same = mainThreadId == afterThreadId;
        Debug.Log($"[CLAIM 06] Same thread: {same}. If true, claim is VERIFIED.");
    }

    // ══════════════════════════════════════════════════════════════════
    // TEST 07 — ConfigureAwait(false) leaves main thread
    // Blog claim (§2.3): "ConfigureAwait(false) explicitly tells the
    //   runtime to NOT capture the synchronization context"
    // ══════════════════════════════════════════════════════════════════
    private async void Test07_ConfigureAwaitFalseLeavesMainThread()
    {
        Debug.Log("───────────────────────────────────────────────────────");
        Debug.Log("[CLAIM 07] ConfigureAwait(false): continuation may NOT be on main thread");
        Debug.Log("  Blog §2.3: 'Continuation runs on thread pool thread'");

        int mainThreadId = Thread.CurrentThread.ManagedThreadId;
        Debug.Log($"  Before await — Thread ID: {mainThreadId}");

        await Task.Delay(500).ConfigureAwait(false);

        int afterThreadId = Thread.CurrentThread.ManagedThreadId;
        Debug.Log($"  After ConfigureAwait(false) — Thread ID: {afterThreadId}");

        bool different = mainThreadId != afterThreadId;
        Debug.Log($"[CLAIM 07] Different thread: {different}. If true, claim is VERIFIED.");
        Debug.Log("  NOTE: It's technically possible (but unlikely) to land on the same thread by coincidence.");
    }

    // ══════════════════════════════════════════════════════════════════
    // TEST 08 — Task.Run: no SynchronizationContext inside
    // Blog claim (§2.3): "Now on thread pool —
    //   SynchronizationContext.Current is null!"
    // ══════════════════════════════════════════════════════════════════
    private async void Test08_TaskRunNoSyncContext()
    {
        Debug.Log("───────────────────────────────────────────────────────");
        Debug.Log("[CLAIM 08] Task.Run: SynchronizationContext.Current is null inside");
        Debug.Log("  Blog §2.3: 'SynchronizationContext.Current is null!'");

        var outerCtx = SynchronizationContext.Current;
        Debug.Log($"  Outside Task.Run — SyncContext: {outerCtx?.GetType().Name ?? "null"}");

        string innerCtxName = null;
        int innerThreadId = -1;
        await Task.Run(() =>
        {
            innerCtxName = SynchronizationContext.Current?.GetType().Name ?? "null";
            innerThreadId = Thread.CurrentThread.ManagedThreadId;
        });

        Debug.Log($"  Inside Task.Run  — SyncContext: {innerCtxName}, Thread ID: {innerThreadId}");

        bool isNull = innerCtxName == "null";
        Debug.Log($"[CLAIM 08] SyncContext is null inside Task.Run: {isNull}. If true, claim is VERIFIED.");
    }

    // ══════════════════════════════════════════════════════════════════
    // TEST 09 — After awaiting Task.Run, back on main thread
    // Blog claim (§2.4): "Back on main thread (context was captured
    //   before Task.Run)"
    // ══════════════════════════════════════════════════════════════════
    private async void Test09_AfterAwaitTaskRunBackOnMainThread()
    {
        Debug.Log("───────────────────────────────────────────────────────");
        Debug.Log("[CLAIM 09] After await Task.Run, continuation is back on main thread");
        Debug.Log("  Blog §2.4: 'Back on main thread (context was captured before Task.Run)'");

        int mainThreadId = Thread.CurrentThread.ManagedThreadId;

        await Task.Run(() =>
        {
            Debug.Log($"  Inside Task.Run — Thread ID: {Thread.CurrentThread.ManagedThreadId}");
        });

        int afterThreadId = Thread.CurrentThread.ManagedThreadId;
        Debug.Log($"  After Task.Run  — Thread ID: {afterThreadId} (main was {mainThreadId})");

        bool same = mainThreadId == afterThreadId;
        Debug.Log($"[CLAIM 09] Back on main thread: {same}. If true, claim is VERIFIED.");
    }

    // ══════════════════════════════════════════════════════════════════
    // TEST 10 — Awaitable: explicit thread switching
    // Blog claim (§3.3): BackgroundThreadAsync/MainThreadAsync
    //   provide explicit thread control
    // ══════════════════════════════════════════════════════════════════
    private async void Test10_AwaitableThreadSwitching()
    {
        Debug.Log("───────────────────────────────────────────────────────");
        Debug.Log("[CLAIM 10] Awaitable: BackgroundThreadAsync / MainThreadAsync thread switching");
        Debug.Log("  Blog §3.3: 'Awaitable provides explicit thread control'");

#if UNITY_2023_1_OR_NEWER
        int mainThreadId = Thread.CurrentThread.ManagedThreadId;
        Debug.Log($"  Start — Thread ID: {mainThreadId}");

        await Awaitable.BackgroundThreadAsync();
        int bgThreadId = Thread.CurrentThread.ManagedThreadId;
        Debug.Log($"  After BackgroundThreadAsync — Thread ID: {bgThreadId}");

        await Awaitable.MainThreadAsync();
        int returnedThreadId = Thread.CurrentThread.ManagedThreadId;
        Debug.Log($"  After MainThreadAsync — Thread ID: {returnedThreadId}");

        bool wentToBackground = mainThreadId != bgThreadId;
        bool returnedToMain = mainThreadId == returnedThreadId;
        Debug.Log($"[CLAIM 10] Went to background: {wentToBackground}, returned to main: {returnedToMain}.");
        Debug.Log($"  If both true, claim is VERIFIED.");
#else
        Debug.Log("[CLAIM 10] SKIPPED — requires Unity 2023.1+");
#endif
    }

    // ══════════════════════════════════════════════════════════════════
    // TEST 11 — UniTaskVoid.Forget() logs exceptions
    // Blog claim (§4.5): "This gets logged, not swallowed!"
    // ══════════════════════════════════════════════════════════════════
    private void Test11_UniTaskVoidForgetLogsException()
    {
        Debug.Log("───────────────────────────────────────────────────────");
        Debug.Log("[CLAIM 11] UniTaskVoid: Forget() logs exceptions, does not swallow");
        Debug.Log("  Blog §4.5: 'This gets logged, not swallowed!'");
        Debug.Log("  EXPECT: UniTask error/exception log below.");

        UniTaskVoidThatThrows().Forget();

        Debug.Log("[CLAIM 11] If a UniTask exception appears above/below, claim is VERIFIED.");
    }

    private async UniTaskVoid UniTaskVoidThatThrows()
    {
        await UniTask.Yield();
        throw new Exception("Test11: Intentional UniTaskVoid exception — should be logged!");
    }

    // ══════════════════════════════════════════════════════════════════
    // TEST 12 — UniTask SuppressCancellationThrow
    // Blog claim (§4.3): "avoids try/catch boilerplate",
    //   returns (cancelled=true, default) on cancellation
    // ══════════════════════════════════════════════════════════════════
    private async void Test12_UniTaskSuppressCancellationThrow()
    {
        Debug.Log("───────────────────────────────────────────────────────");
        Debug.Log("[CLAIM 12] UniTask: SuppressCancellationThrow returns (true, default) on cancel");
        Debug.Log("  Blog §4.3: 'avoids try/catch boilerplate'");

        using var cts = new CancellationTokenSource();
        cts.Cancel(); // cancel immediately

        var (cancelled, result) = await UniTask.Run(
            () => 42,
            cancellationToken: cts.Token
        ).SuppressCancellationThrow();

        Debug.Log($"  cancelled={cancelled}, result={result}");
        Debug.Log($"[CLAIM 12] cancelled=true: {cancelled}. If true, claim is VERIFIED.");
    }

    // ══════════════════════════════════════════════════════════════════
    // TEST 13 — UniTask GetCancellationTokenOnDestroy
    // Blog claim (§4.3): GetCancellationTokenOnDestroy provides
    //   lifecycle-aware cancellation
    // ══════════════════════════════════════════════════════════════════
    private void Test13_UniTaskGetCancellationTokenOnDestroy()
    {
        Debug.Log("───────────────────────────────────────────────────────");
        Debug.Log("[CLAIM 13] UniTask: GetCancellationTokenOnDestroy provides lifecycle cancellation");
        Debug.Log("  Blog §4.3: 'var ct = this.GetCancellationTokenOnDestroy()'");

        // Create a temporary GO, get its token, destroy it, check cancellation
        var tempGo = new GameObject("Test13_Temp");
        var tempMb = tempGo.AddComponent<DummyMono>();
        var ct = tempMb.GetCancellationTokenOnDestroy();

        Debug.Log($"  Before destroy — IsCancellationRequested: {ct.IsCancellationRequested}");

        Destroy(tempGo);

        // Token is not immediately cancelled — it fires at end of frame
        // So we check on next frame via a tiny async helper
        CheckTokenAfterFrame(ct).Forget();
    }

    private async UniTaskVoid CheckTokenAfterFrame(CancellationToken ct)
    {
        await UniTask.Yield(); // wait one frame for Destroy to take effect
        await UniTask.Yield(); // extra frame for safety

        Debug.Log($"  After destroy + 2 frames — IsCancellationRequested: {ct.IsCancellationRequested}");
        Debug.Log($"[CLAIM 13] Token cancelled after destroy: {ct.IsCancellationRequested}. If true, claim is VERIFIED.");
    }

    // ══════════════════════════════════════════════════════════════════
    // TEST 14 — destroyCancellationToken (Unity 2022.2+)
    // Blog claim (§3.5): MonoBehaviour.destroyCancellationToken
    //   fires OperationCanceledException on destroy
    // ══════════════════════════════════════════════════════════════════
    private void Test14_DestroyCancellationToken()
    {
        Debug.Log("───────────────────────────────────────────────────────");
        Debug.Log("[CLAIM 14] destroyCancellationToken: fires when MonoBehaviour is destroyed");
        Debug.Log("  Blog §3.5: 'MonoBehaviour.destroyCancellationToken'");

#if UNITY_2022_2_OR_NEWER
        var tempGo = new GameObject("Test14_Temp");
        var helper = tempGo.AddComponent<DestroyTokenTestHelper>();
        // The helper starts an async wait using destroyCancellationToken
        // Then we destroy it after a short delay
        DestroyAfterDelay(tempGo).Forget();
#else
        Debug.Log("[CLAIM 14] SKIPPED — requires Unity 2022.2+");
#endif
    }

    private async UniTaskVoid DestroyAfterDelay(GameObject go)
    {
        await UniTask.Delay(500);
        Debug.Log("  Destroying test object now...");
        Destroy(go);
        await UniTask.Yield();
        await UniTask.Yield();
        Debug.Log("[CLAIM 14] Check logs above — if OperationCanceledException was caught, claim is VERIFIED.");
    }

    // ══════════════════════════════════════════════════════════════════
    // TEST 15 — async void: exception AFTER await (goes to SyncContext)
    // ══════════════════════════════════════════════════════════════════
    private async void Test15_AsyncVoidExceptionAfterAwait()
    {
        Debug.Log("───────────────────────────────────────────────────────");
        Debug.Log("[CLAIM 15] async void: exception AFTER await — goes to SynchronizationContext");
        Debug.Log("  EXPECT: Error appears in console via UnitySynchronizationContext.");

        await Task.Yield();
        throw new Exception("Test15: Exception AFTER await in async void");
    }

    // ══════════════════════════════════════════════════════════════════
    // TEST 16 — async void: exception BEFORE any await (synchronous part)
    // This is a nuance: the synchronous part before the first await
    // executes inline and CAN be caught by the caller.
    // ══════════════════════════════════════════════════════════════════
    private void Test16_AsyncVoidExceptionBeforeAwait()
    {
        Debug.Log("───────────────────────────────────────────────────────");
        Debug.Log("[CLAIM 16] async void: exception BEFORE first await — can caller catch it?");
        Debug.Log("  This tests a subtle nuance not in the blog.");
        Debug.Log("  In standard C#, sync part of async void still throws to SyncContext, not caller.");
        Debug.Log("  EXPECT: Caller catch should NOT fire. Error via SyncContext instead.");

        bool callerCaught = false;
        try
        {
            AsyncVoidThrowsBeforeAwait();
        }
        catch (Exception e)
        {
            callerCaught = true;
            Debug.Log($"  Caller CAUGHT: {e.Message}");
        }

        Debug.Log($"  Caller caught: {callerCaught}");
        Debug.Log("[CLAIM 16] If caller did NOT catch, async void always routes to SyncContext (even sync part).");
        Debug.Log("  If caller DID catch, the synchronous portion behaves differently than expected.");
    }

    private async void AsyncVoidThrowsBeforeAwait()
    {
        // No await before this throw — still async void though
        throw new Exception("Test16: Exception BEFORE any await in async void");
#pragma warning disable CS0162
        await Task.Yield(); // unreachable, but makes it truly async void
#pragma warning restore CS0162
    }

    // ══════════════════════════════════════════════════════════════════
    // Helper MonoBehaviour for destroyCancellationToken test
    // ══════════════════════════════════════════════════════════════════
    private class DummyMono : MonoBehaviour { }

#if UNITY_2022_2_OR_NEWER
    private class DestroyTokenTestHelper : MonoBehaviour
    {
        private async void Start()
        {
            Debug.Log("  [DestroyTokenTestHelper] Starting async wait with destroyCancellationToken...");
            try
            {
                // This should throw OperationCanceledException when the GO is destroyed
                await Task.Delay(10000, destroyCancellationToken);
                Debug.Log("  [DestroyTokenTestHelper] Wait completed — NOT expected if destroyed early.");
            }
            catch (OperationCanceledException)
            {
                Debug.Log("  [DestroyTokenTestHelper] OperationCanceledException caught! Token works.");
            }
            catch (Exception e)
            {
                Debug.Log($"  [DestroyTokenTestHelper] Unexpected exception: {e.GetType().Name}: {e.Message}");
            }
        }
    }
#endif
}
