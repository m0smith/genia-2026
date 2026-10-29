# #1299 design

Add one ordinary unset Ref admission gate to the shared source. The boom arm
blocks on that gate before its existing division-by-zero. Root sends all four
messages, then sets the gate and invokes the unchanged idle fixture. Thus even
a worker that reaches boom immediately cannot fail before send3 returns. FIFO
ensures1/2 effects precede failure; queue discard suppresses3. No runtime edits.

Regression test (Python-host scheduling mechanics, not portable authority): load
actual shared YAML; allow the worker to progress to either a blocking unset Ref
read or completed failure before returning root's boom send. Event coordination
forces the adverse original schedule without sleeps or polling. Original source
fails before send3 admission; corrected source blocks on gate and passes.
Timeouts on test Event waits are existing-style deadlock safety, not semantic
requirements or production timeout increases. Post-failure send is independently
checked at existing host boundaries without asserting universal diagnostic text.

New tests precede shared-source repair; retain expected results byte-for-byte.
Stress old/new CPP binaries with bounded max8 concurrency and no retries; retain
all outcomes. Independent reviewer must inspect causality, discarded queued work,
negative sends, portable boundary and lack of runtime/oracle weakening.
