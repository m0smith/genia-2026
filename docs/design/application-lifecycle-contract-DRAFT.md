# Host-selected Application Lifecycle — proposed contract (Revision 2)

Status: **PROPOSED — NOT APPROVED — NOT IMPLEMENTED**.

Tracking: [#1271](https://github.com/m0smith/genia-2026/issues/1271).
Architecture evidence: [independent investigation](https://github.com/m0smith/genia-2026/issues/1271#issuecomment-6326759433).
Authorization: [integration decision](https://github.com/m0smith/genia-2026/issues/1271#issuecomment-6326938758)
is GO for contract writing only. Implementation release: **TBD**, unnumbered
infrastructure follow-up; no R29 scope or scheduling commitment.

Revision 2 responds to the five blocking findings (B1–B5) of the
[technical review](https://github.com/m0smith/genia-2026/pull/1272#issuecomment-6327388782),
as triaged in the [integration assessment](https://github.com/m0smith/genia-2026/pull/1272#issuecomment-6327446561).
That review was written by the original author of this draft and is **not**
author-independent review. Revision 2 has not been independently reviewed.

This draft defines proposed behavior only. MUST, MUST NOT and MAY below apply
**if the relevant proposal is approved**, not to existing runtime claims.
Open decisions in section 12 block acceptance and later RED/implementation.
[GENIA_STATE.md](https://github.com/m0smith/genia-2026/blob/6d50a36d23cc4b894f0456ee502deb5d7796e99b/GENIA_STATE.md)
at inspection baseline `6d50a36d23cc4b894f0456ee502deb5d7796e99b` remains
implemented authority, followed by RULES, REPL README, README and executable specs.
The [companion design](application-lifecycle-design-DRAFT.md) contains mapping,
examples, decision cards, evidence and the future validation plan. It **cannot
supply normative behavior missing from this contract**: every externally
observable rule below stands without it. This contract contains no executable
tests and no examples.

## 1. Purpose and terminology

A Genia application is ordinary Genia work executed within a host-selected
lifecycle. `main` is the conventional work entry of the default application
lifecycle, not a language keyword or special call form.

- **Host**: the launcher/embedding selecting execution mode and supplying only
  explicitly authorized capabilities and peers.
- **Entry binding**: the binding resolved for `main` through the entry program's
  existing ownership rules after successful source evaluation.
- **Required arity**: number of non-rest parameters in a declaration. A rest
  declaration can have required arity zero or one; this is not the same as
  having a fixed zero/one-argument signature.
- **Entry eligibility**: pure structural determination of a permitted call
  vector; it does not match values or invoke any callable.
- **Entry plan**: internal captured callable identity, selected required arity,
  argument recipe and safe provenance. It is neither a clause nor public data.
- **Application scope**: one fresh R14 root execution scope for selected work.
- **Peer/owned peer**: existing R14 LifecycleDefinition. A peer is **owned**
  only after its enter returned a valid success **and** that success was
  committed (section 7.4); descriptor presence never confers ownership.
- **Public scope operations**: the source-visible `lifecycle_scope`,
  `lifecycle_child` and `lifecycle_repeat`. They are unchanged in shape.
- **Application completion**: the host-internal consumption of one application
  scope by the launcher (section 6.2). It is not source-visible.
- **Recognized control**: one of the finite recoverable interruption categories
  of section 7.1. It is distinct from a returned Outcome, from an ordinary
  exception, and from forced termination.
- **Primary/cleanup failure**: R14 first-failure and later-unwind-failure roles.
  Control and misuse categories occupy those roles; they do not replace them.
- **Host final streams**: the stdout/stderr (or runtime-owned sinks standing in
  for them) borrowed by the host to emit the final value and diagnostics
  (section 8.3).
- **Application-owned / peer-owned output**: files, sinks or streams opened by
  application code or by an owned peer, other than host final streams.

No new parser syntax, AST/Core IR node, public Genia function/value category,
ambient current scope, DI container, action registry or second execution engine
is proposed. The host adapts R14; portable meaning is fixed here, not inferred
from a particular host's object layout. Private carriers, journals and exception
classes are design choices and are not normative.

## 2. Normative mode boundary

| Mode | Default application activation | Entry/input policy | Ownership and output authority retained |
|---|---|---|---|
| File | Only after successful evaluation and eligible main | Required arity 1, else 0, else source result; section 3 | Candidate root wraps main only; normal CLI value/diagnostic/status policy |
| `-c` | Same as file | Same entry policy; trailing argv rules unchanged | Same root and CLI result policy |
| Pipe | MUST NOT activate this default lifecycle | Existing wrapped stdin/Flow stage execution; no main dispatch | Flow demand/finalization and stage output; no final Flow echo |
| REPL | MUST NOT activate on submission or discovery | Persistent existing submissions; no automatic main | Existing recovery/rendering and session driver |
| Native test | MUST NOT activate during load/discovery/run/report | Existing registered/discovered test invocation, not main | Existing test outcomes/report/status; no added fixtures/hooks |
| Explicit serve | MUST NOT activate this default lifecycle | Existing one-entry-file R8 descriptors; no main | R8 startup/request/shutdown, listener ownership and diagnostics |
| MCP source evaluation | MUST NOT activate | Source-only worker evaluation, empty argv/EOF stdin; no main | Existing restricted profile, envelope, limits and kill/reap |
| Future sessions/notebooks | No activation granted by this contract | Separate session contract must define submissions/close | No persistent/resumable scope or per-cell main inferred |

Parsing, declaration, annotation metadata, import, module loading and callable
discovery MUST NOT implicitly activate an application scope or dispatch main.
Ordinary source evaluation, including module top-level code and annotation
expressions, can execute explicit authorized calls; this is **not universal
import purity**. Main is not dispatched merely because a module defines it.
R8 remains the sole explicit server-mode authority; this draft does not refactor
its coordinator, routing, CORS, listener or request scopes. Source evaluation
and module initialization are distinct from application-scope ownership: the
application scope owns nothing created before it is entered.

## 3. Entry discovery and argument compatibility

### 3.1 Pure selection

After ordinary entry-source evaluation succeeds, the host MUST resolve the entry
binding without invoking user code, running guards/matchers, acquiring resources,
autoloading arbitrary names or calling argv. Eligibility MUST be determined from
ordinary callable declaration structure, without selecting a representative
clause. An alias to an eligible ordinary group is eligible, including an
immutable alias; a lambda, builtin, noncallable, historical explicit-open value,
closed callable or linked view MUST NOT acquire eligibility merely by being
bound to main. Closed/linked support needs its own implemented gate and decision.

For an eligible ordinary group, select required arity 1 when any declaration has
that required arity; otherwise select required arity 0 when present; otherwise
retain the evaluated source result. Rest declarations count at their required
arity. Eligibility MUST NOT mean “any signature capable of accepting one value”
or a fixed-only reinterpretation of historical keys.

The same rule is proposed for future ordinary pattern/guard declarations: their
required arity is structural (fixed tuple length or prefix before rest), never
computed by matching. This prospective rule supersedes Slice C's temporary
legacy-selector boundary only after a separate integration gate, not now.
Mixed legacy/pattern groups are considered as a whole by this future rule;
fixed and rest records at the same required arity do not require picking one.

If no eligible entry exists, no application scope or peers are entered, no argv
call is made by the entry adapter, and the normal source-result path is used.
There is no new missing-main error or fallback invocation.

### 3.2 Capture and argument preparation

Capture the selected callable **identity** before argument preparation; do not
resolve main again after argv or peer callbacks run. Do not freeze, clone or
relink an ordinary group: subsequent permitted changes to that same identity
remain governed by ordinary callable semantics. No new locking/snapshot or
concurrent-call guarantee is introduced.

For required arity 1, resolve/invoke the existing argv binding exactly once using
its existing zero-argument callable behavior. Pass its returned value as **one
argument**, without spreading, coercing, reparsing, enforcing a new string-list
check or substituting the raw OS vector. The ordinary configured argv returns
a list of trailing strings; a legal rebound argv can return another value.
For required arity 0 prepare an empty vector, without invoking argv.

Argument preparation is outside the R14 application scope, after pure selection.
Its explicit calls can have effects, but no application peer owns their cleanup.
Preparation failure prevents entry and follows host diagnostics/status (section
8). Moving this phase inside the scope is a rejected implicit timing change, not
an implementation convenience.

### 3.3 Ordinary invocation, not clause invocation

The R14 work adapter MUST make one ordinary invocation of the captured group with
the prepared vector through the existing call/Outcome/dispatch/TCO semantics.
It MUST NOT invoke an internal arity record, match arguments during discovery,
rerun a guard after candidate selection, or implement specificity/priority rules.
The scope handle is private to the host work adapter, not an extra main argument.

Ordinary fixed-versus-rest shape selection, unit-local first match, ambiguity,
no-matching-case/function diagnostics and permitted effects remain authoritative.
After entry selection, a pattern/guard miss MUST NOT retry main/0 or use the
source result. An empty argv list is still one argument. Recursive calls execute
as ordinary calls to the same identity with existing tail-call behavior; the
launcher does not create a scope per recursive call.

Adopting ordinary invocation can differ from current representative-record
invocation: unified varargs ambiguity and direct-call absence propagation are
intentional **candidate** deltas, not approved by this draft (D1/D2). No adapter
exception may bypass ordinary dispatch to hide those deltas.

### 3.4 Modules and bindings

Only the entry's resolved main binding is considered. Explicit aliases to an
imported ordinary group keep that group's module closure/provenance and may be
selected under the same eligibility rule. Import alone does not select imported
main, activate extension contributions or transfer ownership of the launcher.
Immutability is shallow; it does not freeze the callable's clause accumulation.
Declaration-through-alias restrictions remain owned by Model B, not relaxed by
entry selection. Closed/linked behavior is deferred, not silently emulated.

## 4. Phase and ownership boundary

| Phase | Relative to application R14 scope | Required behavior |
|---|---|---|
| Select mode / acquire and evaluate source | Outside | Existing evaluation/module initialization rules |
| Discover entry / retain fallback | Outside | Pure, no user invocation |
| Prepare arguments / validate structural host peer descriptors | Outside | No application ownership yet; no peer enter during validation |
| Enter scope and peers | Inside | Explicit host-selected peer list, in attachment order |
| Invoke ordinary work / capture value or failure | Inside | One invocation, no launcher arity retries |
| Unwind owned peers / invalidate scope | Inside, before return | Reverse order and first-primary rule |
| Final result/diagnostic/status emission | Outside, after unwind | Section 8; borrowed host final streams only (section 8.3) |

The order **application work → cleanup/unwind → final host emission** is part of
this contract. It is changed only by a separately approved decision; this draft
proposes no such change.

Default peer list MUST be empty. A host embedding MAY explicitly supply existing
R14 peer definitions without introducing a source-visible registry or implicit
configuration lookup. Mere source selection of file/command grants no authority.
Structural descriptor/list/name/collision misuse is rejected before peer entry;
validation MUST NOT run callbacks to determine their effects or signatures.

Module initialization resources, argument-preparation effects, source-created
independent scopes and arbitrary processes are not retroactively owned by main's
scope. A peer that acquires partially then fails before valid successful enter
must compensate its own partial acquisition; the enclosing scope cannot close an
unpublished resource it never owned.

## 5. R14 mapping and state machine

Application execution uses an R14 root, ordered explicit peers, and a work
callable receiving a private handle. Peer enter and exit receive their existing
arguments and narrow primary summary. Context is available only via explicit
lifecycle_context(handle,name), never lexical injection. Main cannot access the
hidden root or create its children without a separately approved explicit
mechanism; this limitation does not justify ambient lookup.

The existing R14 state vocabulary is retained:

```text
created -> entering -> active -> exiting -> completed
created -> entering -> exiting -> failed       (some peers owned)
created -> entering -> failed                  (none owned)
created -> entering -> active -> exiting -> failed
```

With no peers, active proceeds directly to terminal completion/failure; no exit
callback is invented. A recognized control or peer-protocol misuse follows the
applicable failure path, not a new public state. Structural failure before entry
has no live scope. Abrupt termination may prevent any terminal state or result;
it MUST NOT be reported as completed cleanup.

For every **recoverable** terminal path (ordinary return, returned failure,
protocol misuse, recognized control, diagnostic-normalization failure) the scope
handle MUST be invalidated **before** control returns or any error or control is
re-raised. Context access then fails with the established expired-handle
behavior. Invalidation is a lifetime check, not erasure of values already
legitimately read from context.

Child creation remains explicit, synchronous and under an active parent. An
independent source lifecycle_scope is not implicitly a child of the hidden root.
An R14 child failure remains ordinary LifecycleResult data unless work explicitly
escalates it. R8 request and outbound R14 composition is not rewired.

List/Flow repeat and its independent element scopes retain their current
semantics: eager exhaustive List, lazy single-use bounded-demand Flow, fully
unwound element before yield. Outer host context is not ambiently inherited.
Returning a Flow, promise, callback or process does not extend application scope;
resource-dependent computation must complete while its explicit owner is active.
No automatic consumption, materialization or adoption is introduced.

## 6. Peer protocol misuse: public operations versus application completion

This section is a proposed robustness requirement, **not a claim that current
R14 implements it**. Applying it to the shared engine requires D3/D4 approval
and review of all existing consumers; this document does not amend R14 in place.
Anything below that changes an observable public R14 behavior is labeled
**[R14 CHANGE — maintainer approval]** and is collected in section 6.4.

### 6.1 Classification of callback outcomes

| Observation | Class | Public lifecycle_scope/child/repeat today |
|---|---|---|
| enter returns some(any value) | valid success | accepted |
| enter returns err(reason, map) or err(reason) | valid domain failure | returned failed LifecycleResult |
| exit returns some("nil") | valid success | accepted |
| exit returns err(reason, map) or err(reason) | valid domain failure | returned failed LifecycleResult |
| work returns any value, including err(...) | ordinary application data | returned as some(value) |
| callback or work raises an ordinary exception | ordinary failure | returned failed LifecycleResult (work/enter/exit position) |
| enter or exit returns anything other than some/err | **misuse** | raises a TypeError-family error immediately |
| err context present and not a map | **misuse** | raises a TypeError-family error immediately |
| exit returns some(value) with value other than "nil" | **misuse (new)** — accepted today as success | **[R14 CHANGE]** newly rejected |
| err reason that is not a string | not misuse today; accepted | unchanged; stricter reason validation is **not** proposed here (D3 alternative) |

A returned work `err(...)` is **never** misuse, never a lifecycle failure and never
an exit-status input. Distinguishing misuse from domain failure uses only the
structural shape of the callback outcome, never its reason text or contents.

### 6.2 Public operations (normative)

For `lifecycle_scope`, `lifecycle_child` and `lifecycle_repeat`:

1. **Error identity is preserved.** Misuse MUST continue to be **raised** to the
   caller, with the same error family and the same message wording as the
   current runtime for each existing misuse form. It MUST NOT be converted to a
   returned failed LifecycleResult, because a returned failure is ordinary data
   that surrounding application code may ignore, which would change exit status
   and results of otherwise valid programs.
2. **Cleanup and invalidation precede the raise.** Upon classifying misuse the
   engine MUST record the misuse as the failure at that callback's position,
   continue the section 6 unwind of every peer already owned (reverse order,
   each exactly once, never retrying the misusing exit), mark the scope terminal
   and invalidate the handle, and only then raise. **[R14 CHANGE]** Today the
   raise happens immediately: earlier owned peers are not exited and the handle
   remains readable.
3. **Raise-time view.** The raised error identifies only the original misuse.
   Cleanup failures encountered during the post-misuse unwind are not attached
   to the raised error, which gains no new public field. They are preserved in
   the application completion record (6.3) when the scope is the application
   root, and are otherwise not observable.
4. **Ordinary failures and returned data are unchanged**: work or callback
   ordinary exceptions and valid `err` outcomes continue to produce a returned
   failed LifecycleResult with the existing closed keys, and a successful work
   value continues to be retained when only cleanup later fails.
5. **Recognized control** (section 7) re-raises the original control after local
   unwind and invalidation; it does not become a returned LifecycleResult.

A misuse raised through an enclosing scope is an ordinary exception for that
enclosing scope: it becomes the enclosing scope's work failure (class ordinary
failure) under the enclosing scope's own first-primary rule.

### 6.3 Application completion (normative, host-internal)

The application root is consumed only by the launcher, immediately after unwind,
with no application code between the scope's end and the launcher's projection.
It is therefore the only place where a misuse or control occurrence can be
**projected** instead of raised without letting application code ignore it. For
the application root:

- Misuse is classified, cleaned up, invalidated and projected as a failure at
  its callback position, with the fixed identity `lifecycle-peer-protocol-invalid`
  (section 8.2). If the first failure in chronological order was something else,
  that earlier failure stays the **primary** and the misuse is a cleanup
  observation, exactly as for any later exit failure.
- The completion record contains: the root's closed LifecycleResult keys; the
  ordered cleanup observations including any misuse or control that was raised
  rather than returned; the recognized-control identity if any; and the ordered
  nested-scope observations of section 7.3.
- The completion record is not a LifecycleResult extension, a source-visible
  value or a public host API.

The public-versus-application distinction MUST NOT be implemented by two
independent lifecycle algorithms: both consume the same one engine algorithm.

### 6.4 Compatibility consequences requiring explicit maintainer approval

| # | Change to existing public R14 behavior | Direction |
|---|---|---|
| R1 | Earlier owned peers are now exited, in reverse order, before a misuse error is raised | Observable: more cleanup effects run than today; aligns with the R14 cleanup obligation |
| R2 | The handle is invalid (expired-handle behavior) after misuse is raised, where today it stays readable | Aligns with the R14 lifetime rule |
| R3 | exit returning some(value ≠ "nil") is newly rejected (raised as misuse) | **Valid-to-error for any program relying on the permissive acceptance.** Today status ok and normal completion. Not about work values: inspecting work values is never proposed |
| R4 | A recognized control (keyboard interruption) now runs owned exits before propagating, instead of propagating with none run and the handle still active | Observable: previously skipped exits now run |
| R5 | Ordinary exception text in a failed LifecycleResult reason is replaced by the fixed projection only on the **application host diagnostic path**; public LifecycleResult reason text from source-visible scope calls is unchanged by this contract | D5 may separately decide to normalize it |

Alternatives for R3, for decision D3: (a) reject — proposed; (b) retain
permissive acceptance and document it as an R14 deviation, with the application
consumer treating some(non-"nil") exit as success; (c) reject only on the
application root. Option (c) is not recommended because it makes the same peer
valid or invalid depending on its enclosing consumer.

If the maintainers reject R1–R4, the proposed cleanup guarantees (sections 6 and
7) narrow to the public-scope cases that R14 already satisfies, and the
application scope MUST then not advertise those guarantees.

### 6.5 Cleanup obligations

| Event | Work | Required cleanup opportunity, if control remains recoverable |
|---|---|---|
| All enters succeed, work returns any ordinary value | Captured | Each owned peer once, reverse order |
| Enter returns err, raises, is interrupted, or is misuse | Skipped | Only previously owned peers; the failing entry is not owned |
| Work raises or is interrupted | Failed, no result | Every owned peer, reverse order |
| Exit returns err, raises, is interrupted or is misuse | Preserve prior work capture | Continue remaining earlier owned peers; never retry the failing exit |
| Structural descriptor misuse before entry | Not invoked | None owned, none exited; raised without scope |
| Forced process termination / crash / fatal runtime condition | No promised result | No Genia cleanup or invalidation guarantee |

The first failure in enter/work/unwind order is primary, whatever its class
(ordinary, misuse or control). With no earlier failure, the first exit failure
becomes primary; later exit failures are appended in exit-call order. Misuse and
control do not erase an earlier failure. Exit summary remains the R14
status/phase/peer map, without work return, sibling resources or exception
objects. No rollback of arbitrary effects or retry of partially completed cleanup
is implied.

## 7. Interruption and cancellation

### 7.1 Recognized control categories

The set of recognized controls is **finite and closed per host**:

| Category | Meaning | Required recognition |
|---|---|---|
| `interrupt` | User/keyboard interruption (for the Python CLI, the keyboard interrupt) delivered synchronously | Every host that supports interactive interruption |
| `cancel` | Cooperative cancellation or termination request that the host has explicitly translated into a recoverable synchronous event | Only if the host documents such a bridge; none is required |

Everything else is **not** a recognized control and is never converted into one:
process exit requests, generator/coroutine termination, fatal allocation or
runtime failures, forced kill signals, and crashes. A cancellation is never
inferred from a returned none/err, a magic string, a user value, or a peer's
failure reason text. No new Genia cancellation constructor, token, signal API,
portable signal-handling protocol or asynchronous scheduling mechanism is
defined here. A host MUST list its recognized controls in its host documentation
before claiming this contract.

### 7.2 Guarantees (bounded)

A recognized control delivered at a **safe delivery point** MUST stop later
entry/work and give every owned peer its unwind opportunity (6.5). Safe
delivery points are: before a peer's enter callback begins; inside an enter
callback; between enter and the next enter; inside work; before an exit callback
begins; and inside an exit callback.

Not guaranteed, and a host MUST NOT claim otherwise: reliable cleanup after
SIGKILL, process crash, fatal runtime termination, or an exit/work callback that
never returns; cleanup of resources acquired but not yet owned (7.4); any
bound on cleanup duration; delivery promptness while work is running code that
reaches no delivery point.

### 7.3 Per-scope primary precedence and nested propagation

Each scope applies the section 6.5 first-failure rule independently. A control
delivered at a callback occupies that callback's failure position in **that**
scope. An earlier failure in the same scope keeps precedence over a later control;
a later control is then a cleanup observation of that scope.

A recognized control that terminates a scope's local unwind MUST then propagate,
unchanged in identity, out of the public scope operation to its synchronous
caller (6.2 item 5). It MUST NOT be swallowed as a returned child LifecycleResult.
The enclosing scope records the arriving control at **its own** failure position
(its work, enter or exit position, wherever the call happened) under its own
first-primary rule. A child's earlier ordinary failure is not promoted into the
parent's primary.

**Required worked outcome.** Inner scope I runs inside outer scope O's work. I's
work raises ordinary failure F; during I's cleanup an exit of I is interrupted
(K). O has no earlier failure.

1. I: primary = F (work); cleanup list = [K at that exit]; remaining I exits run;
   I invalidated; I does not return a LifecycleResult because K is a control.
2. K propagates into O's work: O's primary = K (work position). O's exits run
   with a summary of status error, phase work, no peer. O invalidated; K
   continues to O's caller.
3. The host observes the application root's primary = K.

Host projection (8.2/8.4): primary = interruption diagnostic, exit status per
8.4 (130 on the Python CLI); then **secondary** observations in chronological
order of occurrence: first I's F as a *nested scope primary failure* (depth and
phase labeled), then any further cleanup failures in unwind order. K is reported
once, as the primary, and the nested entry for I's exit marks it as that same
interruption rather than repeating it. F is therefore preserved and labeled, but
it never becomes O's primary and never determines the exit status.

### 7.4 Ownership commit and delivery boundaries

A peer becomes **owned** at one atomic commit point: after its enter returned a
valid `some(context)`, the engine has recorded the peer as owned and published
its context. The interval from the callback's return to that commit is the
**commit window**.

- A host MUST NOT deliver a recoverable control inside the commit window. If its
  mechanism can defer delivery to just after commit, it MUST do so, and the peer
  is then owned and exited.
- A host that cannot defer delivery in that window (for example, because the
  control can be delivered asynchronously between any two evaluation steps)
  MUST document that a control arriving in the commit window can leave the
  just-acquired resource unowned, and MUST NOT claim the full 7.2 guarantee.
- A control delivered **inside** an enter callback never confers ownership.
  The peer's callback is responsible for compensating its own partial
  acquisition (section 4).

Merely catching a broad host exception category around callbacks does not satisfy
this section.

### 7.5 Interruption during cleanup

- A control delivered during an exit callback records that exit's failure
  (control class) under the 6.5 rule and the remaining earlier owned peers still
  receive their exit. The interrupted exit is never retried.
- A further recoverable request arriving while the scope is unwinding MUST be
  **latched** (at most one remembered) and MUST NOT re-interrupt the same unwind.
  After the unwind and projection complete, a latched request has no further
  effect on that run; it MUST NOT re-enter cleanup.
- A host MAY offer an explicit forced-abort on repeated requests (for example, a
  second keyboard interrupt aborting the process). That is outside R14 and
  outside this guarantee; if it fires, no cleanup completeness is claimed and
  the status remains the one mapped for the first control. A hard-terminating
  supervisor remains a separate host mechanism (7.7).
- A control arriving after unwind completes, during final emission, is handled
  by the host's final emission policy (8.3, 8.4): no scope re-entry, no repeated
  cleanup.

### 7.6 Host exit-status mapping

Exit status derives from the application root's **primary** only (8.4). A control
that is only a secondary observation never changes the status. A host declares
its OS-level mapping; the proposed Python CLI mapping is `interrupt` → 130,
`cancel` → 1 (D4). No portable OS signal convention is defined.

### 7.7 Existing hard supervisors

A host MAY continue using an existing hard-termination supervisor. If it kills a
worker or process, only externally owned cleanup/reaping can be claimed. MCP's
kill/reap cancellation is unchanged and does not become R14 cleanup. A host that
does not deliver a recoverable termination request has no guarantee merely
because a signal was sent.

## 8. Result, diagnostic and host-status normalization

### 8.1 LifecycleResult and ordinary data

Use the existing closed R14 LifecycleResult keys without extension: status,
state, scope, phase, peer, result, primary_failure, cleanup_failures. Application
scope uses the root scope tag. Work return is carried as **some(ordinary value)**;
no work result when skipped/raised. A successful work return remains captured if
only cleanup later fails. Entry/work/exit failures use the existing phase and
peer failure-value structure; no application-specific result variant is added.

The adapter unwraps only that lifecycle-owned result layer. Application some,
none, err, numbers and nested LifecycleResults retain ordinary identity and
rendering. Returned err is not thrown failure; returned number is not exit code.
No default escalation of a child's failed result or collection of failed records.

### 8.2 Diagnostic projection (host-generated diagnostics)

**Scope of this section.** It governs diagnostics **generated by the host or its
adapter** for failures in the application phases: argument preparation, peer
enter, work, peer exit, misuse, control, and final emission. It does not govern:
(a) failures during source evaluation or module initialization **before** the
application phase, whose legacy `Error: …` output is unchanged by this contract
(D5 may extend later); (b) eval-level normalized error data used by shared
`spec/error` cases; (c) text that user code deliberately writes through an
authorized output operation, which is application output that this contract
neither filters nor guarantees.

**Rules.**

1. Trusted fields come only from **structured data supplied by the code that
   raised the diagnostic**, never from parsing `str`, `repr` or message text of
   an exception, and never from a class name alone. A category with no structured
   supplier is projected as the fixed host failure.
2. Projection MUST NOT invoke arbitrary stringification, repr, property access
   or serialization on a failure object to recover a message.
3. Output is composed only from: the stable identity token, the phase label, a
   peer name that passes the identifier-shape check, trusted structural fields
   below, and a logical location.
4. **Logical source location** is limited to: `<command>`; `<pipe>`; the entry
   program operand exactly as the user typed it on the command line; a module's
   logical import name; and line/column within those. A resolved absolute
   host path, the working directory, host line numbers or traceback frames, and
   object identifiers/addresses are never emitted.
5. The legacy prefix `Error: ` is retained on the first line of a failure
   diagnostic. Exact fixed wording of each row is part of D5 approval.

| Identity (stable token) | Applies when | Trusted structural fields permitted | Redacted / never emitted |
|---|---|---|---|
| `no-matching-case` | An ordinary call found no matching case or function | callee name; arity; logical location | argument values, argument lists, matched data |
| `undefined-name` | Name lookup failed | the source identifier; logical location | surrounding values |
| `call-shape` | Wrong argument count or non-callable | callee name if known; expected/actual counts | argument values |
| `builtin-type` | A builtin rejected an argument type | builtin name; parameter position; expected type name | the actual value; any Python type name (a Genia value-category name MAY be given) |
| `lifecycle-scope-expired` | A stale scope handle was used | fixed token only | handle contents |
| `lifecycle-peer-protocol-invalid` | Section 6 misuse | phase; peer name | the offending value, err context |
| `application-peer-failure` | A valid peer `err(reason, context)` | phase; peer name; the reason **only if** it matches the stable-token shape `[a-z][a-z0-9._:-]{0,63}` | context map; any reason that does not match the shape (replaced by the fixed token alone) |
| `application-argument-preparation-failed` | The argv recipe failed | the nested cause identity from this table | all values |
| `application-interrupted` | Recognized `interrupt` | phase | none |
| `application-cancelled` | Recognized `cancel` | phase | none |
| `application-output-failed` | Final emission failed (8.3) | which final stream (`stdout` or `stderr`) | exception text |
| `application-host-failure` | **Synthetic fixed fallback** for any failure not matched above, including unstructured exceptions, resource/memory conditions and any failure while projecting | phase; peer name if known | everything else |

Information that MUST be redacted in every row: caller-supplied arguments,
captured closures, raw peer contexts, protected payloads (R10 carriers stay
opaque), private filesystem paths, host addresses and URLs, environment values,
exception text of any kind, host exception class names, and host handles.

**Diagnostic normalization cannot bypass cleanup.** Classification and projection
run on a guarded, non-effectful path. If they fail for any reason, the same
position receives `application-host-failure`, and the unwind of all owned peers
proceeds exactly as for an ordinary failure. A failure object whose
stringification would itself fail is never stringified.

**Ordering.** One primary diagnostic, then secondary diagnostics: cleanup
failures of the root in exit-call order, then nested-scope observations
(7.3) in chronological order of occurrence, inner scopes before outer. Every
line carries its phase and, where applicable, its peer and scope depth.

**Explicit legacy text changes requiring approval (D5).**

| # | Legacy behavior (Python reference host) | Proposed |
|---|---|---|
| L1 | A grouped-call miss prints `No matching case for function main/1 with arguments [...]`, including argument values | Arguments removed; callee, arity and location kept |
| L2 | A generic exception in main is printed as the exception's own text | Replaced by a categorized or fixed projection |
| L3 | File-mode locations can carry the resolved absolute path | Logical location per rule 4 |
| L4 | Peer-supplied reasons are copied verbatim into LifecycleResult and printed | Printed only if token-shaped (LifecycleResult values themselves unchanged, R5) |
| L5 | `Error: Undefined name: <name>` | **Unchanged** byte-for-byte when the name is a source identifier |

### 8.3 Final output stream ownership

| Resource | Owner | Required lifetime and rules |
|---|---|---|
| Host final streams (borrowed stdout/stderr or the runtime sinks for them) | Host | Valid from before entry until final emission and flush complete. The host borrows them to the application; it never transfers ownership |
| Application-owned output (files/sinks the application or its work opens) | The application, or the peer that owns it | Closed no later than that owner's unwind; never used by the host's final emitter |
| Peer-owned sinks held in a peer context | The owning peer | Opened in enter, closed in exit; the host final emitter MUST NOT write to them |

1. **No application peer may close a host final stream.** Any capability naming a
   host final stream that is handed to work or to a host-supplied peer MUST be a
   non-closing view; a close request through it MUST fail as an ordinary work or
   exit failure and MUST NOT close the stream. A host embedding that supplies a
   peer which closes a final stream violates this contract.
2. The host MUST verify, immediately before final emission, that the final
   streams still accept output; if not, section 8.3 item 4 applies.
3. Output that an application peer needs delivered in the final report is
   **returned as an ordinary work value** and emitted by the host after unwind,
   or fully written during work to the peer's own sink. A peer-owned sink is
   never a substitute for a host final stream.
4. **Final emission failure after cleanup.** The scope is already terminal; the
   host MUST NOT re-enter the scope, repeat any exit or retry cleanup. Behavior:
   - stdout write fails (not quiet broken pipe), with no earlier failure: exit
     status 1; a best-effort `application-output-failed` diagnostic on stderr;
   - stdout quiet broken pipe, no earlier failure: unchanged quiet policy, exit
     status 0 (8.4);
   - an earlier primary failure exists: the primary's status is kept; the
     emission failure is best-effort secondary on stderr;
   - stderr write fails: best effort only. It MUST NOT trigger recursive
     diagnostics or alter the selected primary or status;
   - a recognized control arriving during final emission: no re-entry; status
     per the original primary, or the control's mapping if there was none.
5. Earlier user stdout is not rolled back or transactionally buffered.

### 8.4 Default CLI policy

After full unwind and invalidation:

| Final observation | File/command host behavior |
|---|---|
| Successful selected work or no-main source result | Existing non-nil final debug rendering, exit 0; suppress only existing nil-like absence |
| Successful work returns err | Render ordinary err data, exit 0 |
| Preparation/entry/work/cleanup failure (ordinary or misuse) | Primary diagnostic (8.2) then ordered secondary diagnostics, exit 1; no successful final-value echo |
| Primary recognized `interrupt` | Interruption diagnostic after unwind, exit 130 on the Python CLI; other hosts declare their mapping |
| Primary recognized `cancel` | Cancellation diagnostic after unwind; proposed Python CLI exit 1 |
| Control only as secondary observation | Primary determines status; control added to secondary diagnostics |
| Quiet stdout broken pipe, no other failure | Complete owned unwind, no traceback/diagnostic, exit 0 |
| Quiet broken pipe plus genuine cleanup failure | Cleanup diagnostic on stderr, exit 1; no successful value echo |
| Failure rendering final value after scope completion | Section 8.3 item 4; no re-entry |

Quiet broken pipe is a host output-policy exception to error-status projection,
not a replacement for first-primary ordering. If it occurs in work it is
recorded at the work position; if it occurs only during final emission the scope
has already completed. These status/diagnostic proposals are **not current R14
guarantees**. No new source-visible exit operation or application err-to-exit
policy is introduced. Alternative policies for an embedding need a separate
explicit boundary contract and cannot silently alter the default CLI.

## 9. Compatibility matrix

| Boundary | Proposed disposition | Approval dependency |
|---|---|---|
| Required key 1 over 0; source fallback; legacy rest keys | Preserve structurally, no spread/coercion | D1 confirms future mixed/pattern eligibility |
| Group aliases including immutable/imported alias | Preserve identity/module closure; no declaration authority through alias | D1; Model B ownership remains separate |
| Arbitrary lambda named main | Continue no auto-entry | Any broadening deferred |
| Rebound argv | Call once outside root; retain value and effects | D2 ordinary absence-propagation consequence |
| Current direct arity record → ordinary group | Prospective dispatch/absence differences explicit, never hidden | D1/D2 required; #1269 D1 alone is not entry integration approval |
| Future pattern main | Structural arity selection then ordinary dispatch once; no cross-arity fallback | Model B execution gate plus D1 |
| Public scope misuse | Still **raised**; cleanup and invalidation first (6.2) | D3 (R1, R2) |
| exit → some(non-"nil") | Newly rejected as misuse | D3 (R3) — valid-to-error |
| Keyboard interruption in a public scope | Owned exits run, then control re-raised | D4 (R4) |
| Raw host exception text | Replaced by the 8.2 projection on the host diagnostic path | D5 (L1–L4) |
| Broken pipe and cleanup | Retain failure order, report cleanup, exit 1 only for genuine cleanup failure | D6 |
| Final stream ownership | Host-borrowed, non-closable by peers | D6/D7 |
| Other modes and initialization | No automatic main-root activation or ownership expansion | Preserved scope lock |

## 10. Security and protected values

No new authority is granted by selecting the default lifecycle. R10 protected
carriers/declassification and R13 provider behavior remain authoritative.
Configuration peers capture already constructed providers, never acquire/refresh
or inject them into main. A hidden provider is not source-accessible without an
existing explicit handle. Do not compensate with ambient lookup.

Read-only context lookup is not deep immutability: existing Ref/Cell/capability
values retain their authority. A peer is responsible for what context it exposes;
private resources must not be published accidentally. Scope expiry prevents late
access through the handle, not revocation of copied authority or erasure of values.
Returned lazy values do not keep the scope alive. Host-owned cleanup does not
make untrusted code a sandbox or authorize arbitrary external effects. The 8.2
projection protects **host-generated** diagnostics only.

## 11. Portability, R16 applicability and merge conditions

Portable obligations are selection/ordinary dispatch, R14 ownership/failure
ordering and safe outcome projection. OS signal delivery, Python exception
mechanics and supervisor kill/reap are host realizations, with explicit limits.
Reuse R16 vocabulary, protocol and evidence. **No new conformance system,
registry, profile or "application" flag is created by this contract.**

### 11.1 Required CLI behavior (separate from everything below)

The following is **required** conformance behavior today and MUST NOT be
relabeled optional, tagged, skipped, or moved behind a new capability in order to
obtain a passing host-parity report:

- `cli_file_mode` and `cli_command_mode` are in the manifest's
  `required_capabilities`. Shared CLI cases without a `requires:` entry, notably
  the existing file-mode `main` argv case, the command-mode argv/double-dash
  cases and the command-mode runtime-error case, are baseline required cases.
- The legacy entry floor (main/1, then main/0, then source result; argv as one
  list argument; fallback; aliases) is therefore required behavior for every
  host that claims the required CLI capabilities.
- The 8.2 projection changes stderr only for application-phase failures; the
  existing required `error_runtime` case (a source-evaluation undefined name)
  is outside it and unchanged.

### 11.2 Optional lifecycle capabilities (independently claimable only)

Application lifecycle behavior that no required case observes (peer ownership
with host-supplied peers, interruption mapping, host-final-stream lifetime) is
**host-embedding behavior with no source-visible surface**; it is not currently
expressible as a shared source-only case. Such behavior stays host-local
(Python host tests) until a portable observable exists. Whether any genuinely
independent portable lifecycle surface exists, and whether it needs a new name in
the existing optional-capability vocabulary, is **a separate decision requiring
separate authorization** (D8). Without that authorization no lifecycle
capability is advertised.

### 11.3 Python support

Python is the reference host. The proposed behavior is **not implemented** there.
R14 normal synchronous paths exist; the section 6–8 hardening does not. No
Python claim changes with this contract.

### 11.4 Known C++ limitations

The bounded C++ host has no demonstrated R14 lifecycle, protected-resource, MCP,
Model B local ordinary-pattern or TCO support, and its file-operand CLI path is
not evidenced to accept trailing program arguments; STATE limits argv to pipe
mode. Historical R24–R27 zero-failure counts are not evidence for this feature.
No C++ parity or release is promised. `unsupported` is a distinct count that
**never** equals PASS.

### 11.5 Shared-spec acceptance requirements

Before any implementation merge: shared contract/conformance evidence leads
implementation; changed or added shared expectations are accepted on **both**
hosts or covered by the explicit process in 11.6; and pass/unsupported/failure
counts are reported separately. Changing an existing required case's expected
output (for example any CLI stderr expectation) is a conformance migration and
counts as a required-behavior change for both hosts.

### 11.6 Temporary exceptions and merge-blocking conditions

Under the current process, `spec/known_host_gaps.json` and the host-parity gate
accept gap entries **only for names in `optional_capabilities`**; the loader
rejects any other name, and the gate compares only the optional set. **No
mechanism exists today to excuse a failing or unsupported required case.**
Therefore:

- Implementation or merge MUST remain **blocked** if the required CLI cases would
  fail, or would remain unsupported, on a host that claims the required
  capabilities, unless a **separately authorized** decision defines a
  required-case exception or migration mechanism with owner, tracking issue,
  affected host, exact cases, reason and removal condition. This contract does not
  invent that mechanism and does not grant that authorization.
- "Python first with an optional gap" is not a valid disposition for required
  behavior.
- A green optional-capability parity report does not demonstrate required CLI
  parity and MUST NOT be presented as such.
- Any optional lifecycle capability that is separately authorized requires an
  exact issue-backed gap entry, as the existing process already specifies, before
  merge.

### 11.7 Exclusions and synchronization

Excluded: source-visible application APIs, parser/IR changes, global lifecycle,
DI/service container, arbitrary phase graphs, annotation hooks, implicit imports,
R8 replacement, new Flow/result system, async scheduler/supervision/distribution,
public cancel tokens, resumable scopes, automatic materialization/adoption,
implicit config acquisition, arbitrary lambda/closed/linked entry support,
release number or R29 commitment. Persistent sessions belong to their separate
contract; child access to the hidden root requires a new explicit need and gate.

After future executable verification, a change MUST synchronize `GENIA_STATE.md`,
`GENIA_RULES.md`, `GENIA_REPL_README.md` and `README.md`, the semantic facts and
MCP language profile, host documentation, applicable release/roadmap material
and executable evidence. This draft updates none of those surfaces to claim
implementation. Slice C PR #1270, U2 and its RED gate remain independent and
unchanged.

## 12. Decision register D1–D8 and acceptance boundary

Every row is a **proposal requiring maintainer decision**, not an approval.
Architecture A and permission to draft were approved; none of the choices below
is inferred from that permission. Recommendations are advisory. Each decision
has a card with a concrete example in the
[companion design, section 10](application-lifecycle-design-DRAFT.md#10-decision-cards-d1d8).

| ID | Question | Current behavior | Proposed behavior | Compatibility consequence | Recommendation | Needed before |
|---|---|---|---|---|---|---|
| D1 | May main be selected by structural required arity and invoked as a whole ordinary group? | Direct call of the key-1 then key-0 arity record | Structural eligibility; one ordinary whole-group call | A unified-varargs group (`main(..a)` plus `main(x,..r)`) valid today becomes an ordinary ambiguity; pattern/mixed groups become newly eligible | Approve, disclosing the varargs change | Acceptance, and before integration RED |
| D2 | Is rebound `argv()` honored and main's identity kept live, accepting ordinary absence propagation? | Rebound argv called, record called directly (absence ignored) | Capture identity; call argv once outside the scope; ordinary call | A rebound argv returning none/nil yields absence instead of main's value | Approve, disclosing the absence change | Acceptance, and before integration RED |
| D3 | Do public misuse raises stay raises (after cleanup), and is `exit → some(non-"nil")` newly rejected? | Raise at once without cleanup; some(99) exit accepted | Keep raising; cleanup and invalidation first; reject some(non-"nil") | R1–R4 (6.4); some(99) valid-to-error | Approve raise-after-cleanup; approve R3 only with explicit acknowledgement | Acceptance and R14-hardening RED |
| D4 | What are the bounded interruption guarantees and nested projection? | Interruption skips cleanup and leaves the handle active | Section 7: closed control set, safe points, commit window, latch, nested projection | Exits that were skipped now run; 130/1 mapping | Approve the bounded section 7 guarantees; defer async cancellation and any broader signal set | Acceptance and R14-hardening RED |
| D5 | What diagnostic projection and legacy text changes are accepted? | Exception text printed, grouped-miss arguments included | The 8.2 table with fixed fallback; L1–L4 | Argument and path redaction; less detail for unmapped categories | Approve the table and L1–L5; grow the category list only by later approval | Acceptance and implementation RED |
| D6 | Which output and first-primary policy applies, and who owns final streams? | Quiet broken pipe exits 0 | First-primary and quiet broken pipe unchanged; genuine cleanup failure visible; host final streams non-closable | Cleanup failure after quiet pipe now exits 1 | Approve with the 8.3 ownership rules | Acceptance and implementation RED |
| D7 | Is the adapter a thin host layer with no new source surface or ambient scope? | No application scope exists | Thin adapter over R14; empty default peers; no hidden-root access for main; init and preparation outside the scope | None for source programs | Approve | Acceptance |
| D8 | How is R16 applicability handled for required CLI behavior? | Optional-gap machinery accepts optional names only | Separate required-CLI gate (11.1, 11.6); no relabeling; no new framework | Merge blocked until a required-case path is separately authorized | Approve the separation; do not authorize any exception now | Before RED and before merge |

Stop at proposed contract/design publication. This author does not approve the
contract or authorize tests or production work. An exact-head review by a
**different** reviewer is required (not the author of this draft or of its
technical review), followed by a maintainer gate.
