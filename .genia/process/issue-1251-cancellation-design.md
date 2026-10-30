# POSIX transport cancellation design

Keep the existing subprocess.run path on non-POSIX. For POSIX, one small
documented helper uses Popen(start_new_session=True), identical input/capture/
cwd/env, and communicate with the unchanged caller timeout. On any cancellation
or communicate exception, killpg(adapter.pid,SIGKILL), tolerate only an already
gone group, wait/reap the direct adapter and re-raise the original exception.
run_adapter_request retains its timeout classification, partial diagnostics and
all normal response validation. No inherited shell or ambient group is killed.

RED is a Linux host-mechanics regression with an isolated subreaper controller:
real adapter stub spawns a blocking child, writes partial stdout and records PID.
After a short unit transport timeout, assert TIMEOUT and preserved partial text,
then verify no live same-group descendant remains. Observe/reap exits in the
controller and always terminate/reap a surviving test child in finally. The
observation bound is test cleanup safety, not an increased request deadline.
Before correction, the child remains live and the assertion fails. Existing
protocol tests cover successful/unsupported/malformed/crash/direct-timeout paths.

The test belongs in Python host-internal OS transport mechanics, not a shared
Genia semantic spec. Linux process-state observation is explicitly scoped;
the production POSIX helper uses standard process groups. Preserve all existing
markers/oracles/baselines. Unit artificial timeout does not alter any real
conformance or diagnostic request's10s setting.

After committed RED and minimal correction: targeted transport/runner/Python
adapter tests, checker/lint, separate independent maintainability/behavior
review; one predeclared resource-envelope acceptance pair with all1044 cases,
fixed200Python/1000C++fixture and8R20 samples, concurrency2, no other test/build.
No global auto-concurrency policy, runtime optimization or retry is added.
