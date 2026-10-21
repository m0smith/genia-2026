# Host-selected Application Lifecycle — proposed contract

Status: **PROPOSED — NOT APPROVED — NOT IMPLEMENTED**.

Tracking: [#1271](https://github.com/m0smith/genia-2026/issues/1271).
Architecture evidence: [independent investigation](https://github.com/m0smith/genia-2026/issues/1271#issuecomment-6326759433).
Authorization: [integration decision](https://github.com/m0smith/genia-2026/issues/1271#issuecomment-6326938758)
is GO for contract writing only. Implementation release: **TBD**, unnumbered
infrastructure follow-up; no R29 scope or scheduling commitment.

This draft defines proposed behavior only. MUST, MUST NOT and MAY below apply
**if the relevant proposal is approved**, not to existing runtime claims.
Open decisions in section 12 block acceptance and later RED/implementation.
[GENIA_STATE.md](https://github.com/m0smith/genia-2026/blob/6d50a36d23cc4b894f0456ee502deb5d7796e99b/GENIA_STATE.md)
at inspection baseline `6d50a36d23cc4b894f0456ee502deb5d7796e99b` remains
implemented authority, followed by RULES, REPL README, README and executable specs.
The [companion design](application-lifecycle-design-DRAFT.md) contains mapping,
examples, evidence and the future validation plan; this contract contains no
executable tests.

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
- **Peer/owned peer**: existing R14 LifecycleDefinition; ownership is established
  only by a valid successful enter outcome, never descriptor presence.
- **Recoverable control interruption**: host-recognized keyboard/cooperative
  cancellation delivered synchronously where execution can still unwind. It is
  distinct from an ordinary returned Outcome and from forced termination.
- **Primary/cleanup failure**: R14 first-failure and later-unwind-failure roles;
  host interruption/protocol categories do not replace their ordering.

No new parser syntax, AST/Core IR node, public Genia function/value category,
ambient current scope, DI container, action registry or second execution engine
is proposed. The host adapts R14; portable meaning is fixed here, not inferred
from a particular host's object layout.

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
its coordinator, routing, CORS, listener or request scopes.

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
Preparation failure prevents entry and follows host diagnostics/status. Moving
this phase inside the scope is a rejected implicit timing change, not an
implementation convenience.

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
| Final result/diagnostic/status emission | Outside, after unwind | Section 8; no late scoped-resource use |

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
callback is invented. A recoverable interruption or runtime protocol misuse
follows the applicable failure path, not a new public state. Structural failure
before entry has no live scope. Abrupt termination may prevent any terminal state
or result; it MUST NOT be reported as completed cleanup.

For every recoverable terminal path the scope handle MUST be invalidated before
control returns or an error/control interruption is re-raised. Context access
then fails with the established expired-handle behavior. Invalidation is a
lifetime check, not erasure of values already legitimately read from context.

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

## 6. Peer protocol misuse and cleanup obligations

This section is a proposed robustness requirement, **not a claim that current
R14 implements it**. Applying it to the shared engine requires D3/D4 approval
and review of all existing consumers; this document does not amend R14 in place.

A valid enter returns existing some(context) or err(reason,context). A valid exit
returns the R14 contracted some("nil") or err(reason,context). Omitted err context
normalizes to the existing empty map; a supplied non-map context is invalid.
Reason must satisfy the contracted string shape. Success wrappers must satisfy
the existing contracted shape without forcing protected/lazy values.

An invalid peer outcome MUST be classified as **protocol misuse**, never an
ordinary work err and never silently treated as success. It produces a safe
failure at that peer's enter/exit position, using the existing failure envelope;
proposed stable reason is `lifecycle-peer-protocol-invalid` with no raw payload
in diagnostic context. Host-native exception class is not portable semantics.
If such validation itself cannot safely inspect a malformed value, use the same
fixed failure; do not stringify it. Tightening permissive exit handling needs D3.

| Event | Work | Required cleanup opportunity, if control remains recoverable |
|---|---|---|
| All enters succeed, work returns any ordinary value | Captured | Each owned peer once, reverse order |
| Enter returns err, raises or has malformed outcome | Skipped | Only previously owned peers; failing entry is not owned |
| Work raises or recoverably cancels | Failed, no result | Every owned peer, reverse order |
| Exit returns err, raises, interrupts or has malformed outcome | Preserve prior work capture | Continue remaining earlier owned peers; never retry failing exit |
| Structural descriptor misuse before entry | Not invoked | None owned, none exited |
| Forced process termination / crash | No promised result | No Genia cleanup or terminal-invalidation guarantee |

The first failure in enter/work/unwind order is primary. With no earlier failure,
first exit failure becomes primary; later exit failures are appended in exit-call
order. Misuse does not erase an earlier failure. Exit summary remains the R14
status/phase/peer map, without work return, sibling resources or exception objects.
A malformed summary/normalization failure must not strand remaining owned peers;
use a safe fixed failure at the original phase. No rollback of arbitrary effects
or retry of partially completed cleanup is implied.

## 7. Interruption and cancellation

A caught keyboard interrupt, explicit host-recognized cooperative cancellation,
or host termination request translated into a recoverable synchronous control
interruption MUST stop later entry/work and give owned peers their section 6
unwind opportunity. A cancellation is never inferred from returned none/err,
a magic string or user value. No new Genia cancellation constructor/token/API, portable signal-handling
protocol or asynchronous scheduling mechanism is defined here.

The first recorded interruption occupies the failure position at the callback
where it is delivered. Interruption during exit records that exit's failure and
continues remaining cleanup. An earlier failure in the same scope keeps precedence over later
interruption; a pending interrupt does not silently override that primary. A
child scope's earlier ordinary failure is not automatically promoted to its
parent: each scope keeps R14's own primary ordering. Recognized control still
propagates through enclosing synchronous scopes after local unwind, rather than
being swallowed as a successful ordinary child return.
Cooperative host delivery must not repeatedly interrupt the same unwind; further
requests may be latched until unwind completes. An uncontrolled second signal,
non-returning callback or fatal runtime condition can prevent cleanup, and the
host must not claim otherwise. No deadline or bounded cleanup duration is promised.

A host MAY continue using its existing hard termination supervisor; if it kills
a worker/process, only externally owned cleanup/reaping can be claimed. MCP's
kill/reap cancellation is unchanged and does not become R14 cleanup. A host that
does not deliver a recoverable termination request has no new guarantee merely
because a signal was sent.

Proposed private normalization uses fixed reasons `application-interrupted` for
keyboard interruption and `application-cancelled` for recognized cooperative
cancellation. Original host control identity is retained privately for final
status; it is not a new LifecycleResult field or public capability. Fatal host
exit/SystemExit/generator termination MUST NOT be indiscriminately converted to
these recoverable events. A separately reviewed host bridge must enumerate which
controls it handles (D4), not blanket-catch and suppress every fatal condition.

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

### 8.2 Diagnostic trust boundary

Established safe Genia diagnostics may cross the host boundary with their
language category, safe message and logical source location. Opaque host
exceptions MUST use a non-sensitive fixed reason, proposed
`application-host-failure`. Normalization MUST NOT invoke arbitrary exception
stringification, repr, property access or serialization to recover a message.
If normalization fails, keep the original failure position and use the same safe
fixed reason. A trusted host-specific diagnostic adapter must explicitly permit
fields; Python exception class membership alone does not make str(error) safe.

Never expose exception addresses, absolute host paths, captured args/closures,
raw peer contexts, host handles or protected payloads in failure output. Peer
supplied reason/context stays subject to existing protected-value rules; final
host diagnostics MUST use a safe projection rather than dumping the full result
or arbitrary context. Primary and cleanup phase/peer positions and safe reason
remain distinguishable and deterministically ordered. Proposed exact diagnostic
wording and safe legacy-compatibility boundary require D5 approval.

### 8.3 Default CLI policy (proposed choices D4/D6)

After full unwind/invalidation:

| Final observation | File/command host behavior |
|---|---|
| Successful selected work or no-main source result | Existing non-nil final debug rendering, exit 0; suppress only existing nil-like absence |
| Successful work returns err | Render ordinary err data, exit 0 |
| Entry/preparation/work/cleanup failure | Safe primary diagnostic followed by ordered safe cleanup diagnostics, exit 1; no successful final-value echo |
| Primary recoverable keyboard interrupt | Safe interruption diagnostic after unwind, exit 130 on the Python CLI; other hosts declare their OS mapping without changing primary order |
| Primary recognized cooperative cancellation | Fixed cancellation diagnostic after unwind; proposed Python CLI exit 1, not a portable OS signal convention |
| Secondary interruption after existing primary failure | Retain primary status, add ordered safe cleanup/control observation; do not replace primary |
| Quiet stdout broken pipe, no other failure | Complete owned unwind, no traceback/no noisy diagnostic, exit 0 |
| Quiet broken pipe plus genuine cleanup failure | Keep first failure internally; expose ordered safe cleanup diagnostic on stderr, exit 1; no successful value echo |
| Failure rendering final value after scope completion | Host emission failure, exit 1, with no re-entry/repeated cleanup; quiet broken pipe exception retains its policy |

Quiet broken pipe is a host output-policy exception to error-status projection,
not a replacement for R14 first-primary ordering. If it occurs in work it is
recorded at work position and exits see error summary; if it occurs only during
final emission the scope already completed. Stderr failure is best-effort output
and MUST NOT trigger recursive diagnostics or change the selected primary.
Earlier user stdout is not rolled back or transactionally buffered.

These status/diagnostic proposals are **not current R14 guarantees**. No new
source-visible exit operation or application err-to-exit policy is introduced.
Alternative policies for an embedding require a separate explicit boundary
contract and cannot silently alter the default CLI.

## 9. Compatibility matrix

| Boundary | Proposed disposition | Approval dependency |
|---|---|---|
| Required key 1 over 0; source fallback; legacy rest keys | Preserve structurally, no spread/coercion | D1 confirms future mixed/pattern eligibility |
| Group aliases including immutable/imported alias | Preserve identity/module closure; no declaration authority through alias | D1; Model B ownership remains separate |
| Arbitrary lambda named main | Continue no auto-entry | Any broadening deferred |
| Rebound argv | Call once outside root; retain value and effects | D2 ordinary absence-propagation consequence |
| Current direct arity record -> ordinary group | Prospective dispatch/absence differences explicit, never hidden | D1/D2 required; #1269 D1 alone is not entry integration approval |
| Future pattern main | Structural arity selection then ordinary dispatch once; no cross-arity fallback | Model B execution gate plus D1 |
| Protocol-invalid callback / interruption | Preserve ownership and terminal handle guarantees prospectively | D3/D4; bounded R14 hardening dependency |
| Raw host exception text | Replace with safe fixed projection; keep approved safe Genia diagnostics | D5 |
| Broken pipe and cleanup | Retain failure order, report cleanup, exit 1 only for genuine cleanup failure | D6 |
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
make untrusted code a sandbox or authorize arbitrary external effects.

## 11. Portability, exclusions and future gates

Portable obligations are selection/ordinary dispatch, R14 ownership/failure
ordering and safe outcome projection. OS signal delivery, Python exception
mechanics and supervisor kill/reap are host realizations, with explicit limits.
No C++ application-lifecycle, R14/resource, Model B or TCO claim follows from
bounded CLI capability advertisement. Reuse R16 vocabulary/protocol/evidence.
Unsupported is not passing conformance. Before future implementation merge,
affected hosts must implement or carry approved issue-backed exact gaps with
host, affected cases/area, owner, reason and removal condition. Required CLI
regressions cannot be hidden behind an optional application capability (D8).

Excluded: source-visible application APIs, parser/IR changes, global lifecycle,
DI/service container, arbitrary phase graphs, annotation hooks, implicit imports,
R8 replacement, new Flow/result system, async scheduler/supervision/distribution,
public cancel tokens, resumable scopes, automatic materialization/adoption,
implicit config acquisition, arbitrary lambda/closed/linked entry support,
release number or R29 commitment. Persistent sessions belong to their separate
contract; child access to hidden root requires a new explicit need and gate.

After future executable verification, synchronize implemented authorities,
semantic facts, MCP language profile, host docs and roadmap/release material.
This draft updates none of those surfaces to claim implementation. Slice C PR
#1270, U2 and its RED gate remain independent and unchanged.

## 12. Open decision register and acceptance boundary

Every row is a **proposal requiring maintainer decision**, not a new approval.
Architecture A and permission to draft were approved; none of the choices below
is inferred from that permission. Independent review may revise them first.

| ID | Proposed choice | Required decision before acceptance/RED |
|---|---|---|
| D1 | Structural required-arity eligibility across ordinary records, legacy rest keys retained; whole-group invocation even when ordinary dispatch yields a new ambiguity | Approve future mixed/pattern/rest integration and exact entry deltas; preserve #1269 U2 until integration authorized |
| D2 | Capture callable identity; invoke rebound argv once outside scope, no added coercion; ordinary call absence propagation applies | Acknowledge absence-returning argv delta and live-group mutation timing, or revise policy without hidden dispatcher bypass |
| D3 | Malformed peer outcomes become safe protocol failures at original position, remaining cleanup runs; enforce contracted exit some("nil") | Approve misuse-vs-ordinary-result distinction, diagnostic reason and any tightened validation/legacy misuse delta |
| D4 | Bounded shared-engine hardening plus explicit host control bridge; terminal invalidation; first-primary control status and Python 130/1 mapping | Enumerate recoverable controls, nested scope behavior, deferred/repeated signal limits; no blanket fatal-exception suppression |
| D5 | Fixed opaque-host diagnostics and explicit safe Genia projection; normalization itself cannot skip cleanup | Approve safe diagnostic/category compatibility and wording without raw exception text |
| D6 | Quiet broken pipe remains 0 after cleanup; genuine cleanup failure is visible and exits 1 while primary order stays intact | Approve combined output/cleanup precedence and final-emission behavior |
| D7 | Thin host adapter, empty default peers, no source API; no hidden-root access by main; initialization/preparation outside root | Confirm minimal lifetime/scope and hardening dependency; no change to R8 or other modes |
| D8 | Existing R16 applicability and exact owned host gaps; release TBD | Approve feasible host-gap/mandatory-CLI handling before RED; no premature optional capability or parity claim |

Stop at proposed contract/design publication. This author does not approve the
contract or authorize tests/production work. Later independent Codex review must
inspect these choices and companion evidence, followed by a maintainer gate.
