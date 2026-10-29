# #1299 implementation and GREEN evidence

RED commit:1c885db8 (schedule regression fails at root send3). Minimal repair:
boom evaluates `ref_get(admitted) / 0`; the unset Ref is set to1 only after all
four sends return. Integer1 preserves the original failing numerator and exact
expected stdout/stderr/exit. No runtime/adapters/capability/classification edits.
A block-arm spelling was rejected as UNSUPPORTED in independent design probing;
expression spelling uses the selected host's approved existing subset.

New old-fixture reproduction:200 once-only requests per binary,max8 concurrent:
previous1af65:191PASS/9FAIL; selected1f338866:198PASS/2FAIL. All failures retained,
statusok/exit1/emptystdout/Error: send: process is failed. These supplement,
not replace, historical966/34 and970/30 per1000;198/2 each per200;294/1/749full.

Corrected fixture stress, no retries or sleeps, max8 concurrent:
- selected1f338866 batch1:1000PASS/0 other classes.
- previous1af65 batch1:1000PASS/0 other classes.
- selected1f338866 batch2:1000PASS/0 other classes.

Python fixture tests:6PASS; nearby concurrency tests including previous5fixture
checks:33PASS before adding final negative. New no-sleep negative settles a
failed worker then checks exact Python error/exit1 and unreachable print.
Selected C++ existing native `R25 post-failure Process send is a normalized
runtime error`:1case/4assertionsPASS, exact Error: send: process is failed.
Different host diagnostic wording is preserved, not made a new universal oracle.
Portable FIFO/fail-stop truth stays in the repaired shared YAML. No newcase or
expected value is added/removed. Full final-head host suites belong to the
integration gate; this evidence alone does not certify #1270 or close #1299.

Documentation review: five authority documents keep existing runtime semantics;
no semantic/profile/book/cheatsheet expansion is warranted for fixture ordering.
STATE remains42996words on main-based development branch; integration wordcount
must be checked separately. Historical release evidence is not rewritten.
