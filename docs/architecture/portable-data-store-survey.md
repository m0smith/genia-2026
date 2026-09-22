# Portable Data Store Architecture Survey

Status: Planning/design survey — non-authoritative. `GENIA_STATE.md` remains final authority for implemented behavior. Nothing in this document makes a data-store API, syntax, provider, or capability implemented.

## Purpose

R32 must not accidentally define "database" as SQL, JDBC, ODBC, mutable tables, or one host's driver model. This survey records the architectural constraints that should drive the R32 contract before implementation begins.

The product goal is not universal query translation. It is a stable Genia data boundary in which ordinary values, Flow, Sheet, Outcome, configuration/secrets, and lifecycle semantics remain the application model while provider capabilities describe where and how data is stored.

## Systems surveyed

| Family | Representative systems | Useful lesson | Constraint for Genia |
|---|---|---|---|
| Relational driver APIs | JDBC, ODBC | Explicit connection/provider boundaries, parameterized statements, transactions, cursors | JDBC/ODBC are provider mechanisms, not portable Genia semantics |
| Embedded relational | SQLite | Zero-infrastructure CRUD, SQL, transactions, deterministic local proving | SQLite is a proving/default provider; its transaction and SQL semantics must not define the abstraction |
| Embedded analytical | DuckDB | In-process analytical SQL and columnar/vectorized execution | Analytical/columnar providers should compose naturally with Sheet without making Sheet an implicit query engine |
| Columnar connectivity | Arrow ADBC | Cross-language database connectivity with Arrow-native bulk interchange | Strong candidate for efficient Sheet interchange, but batching/Arrow layout must not become observable Genia semantics |
| Document | MongoDB | Nested documents, aggregation, transactions, change streams | Stored values need not be rows; nested Genia values and change feeds must remain possible |
| Key/value | DynamoDB | Key-oriented operations, conditional writes, transactions, pagination, Streams, optional PartiQL | Portable semantics cannot assume tables behave relationally or that SQL is the universal query language |
| Immutable/Datalog | Datomic | Immutable database values, transactions as data, temporal query, transaction reports | The core must not assume "database = mutable connection + CRUD"; snapshot/time semantics must remain representable |

Redis and similar key/value systems are useful secondary checks, but R32 does not need to ship every provider to establish the boundary.

## Architectural conclusions

### 1. The portable abstraction is a capability-bearing data store

Working planning name: `DataStore`.

The contract should define an opaque, ordinary Genia value representing authority to interact with one configured data store. It should be passable, bindable, returnable, and test-substitutable without exposing host connection objects.

Do not freeze the final public name or syntax in roadmap material. The R32 contract must settle naming.

Provider families may advertise truthful capabilities such as read/source, write, query, transaction, change feed, relational, document, key/value, or temporal behavior. Capability discovery must not imply that every provider supports every operation.

### 2. Values are the portability boundary

The strongest common denominator is not SQL or CRUD. It is conversion between provider data and Genia values.

Multi-value reads should compose with `Flow<Value>` where incremental consumption is available. Materialized tabular data should continue to use the existing explicit Sheet boundary. R32 must not add implicit Sheet-to-Flow, Flow-to-Sheet, or row coercions.

A representative composition target is:

```text
DataStore source
  -> Flow<Value>
  -> existing validation / pattern / transformation stages
  -> explicit collect_sheet when tabular materialization is desired
  -> optional DataStore sink
```

This is a design target, not implemented syntax.

### 3. Do not promise universal CRUD semantics

SQL UPDATE, Mongo document replacement/update, DynamoDB conditional item mutation, and Datomic assertion/retraction are not the same operation.

R32 may define a narrow portable read/write substrate only where the contract can state exact cross-provider semantics. Richer mutation must remain capability-specific rather than being forced through misleading universal CRUD names.

### 4. Query is a capability, not a universal language

SQL, Mongo aggregation, DynamoDB expressions/PartiQL, and Datalog have materially different semantics.

R32 should provide an explicit query boundary while keeping query language/dialect values provider-specific. It must not introduce Genia SQL syntax, an ORM, a universal query AST, or automatic SQL/Datalog/Mongo translation unless a later separately approved release establishes such semantics.

Parameterized query/input binding is mandatory wherever a provider query language supports parameters; application values must not require unsafe string interpolation.

### 5. Change feeds belong in the initial architecture

MongoDB change streams, DynamoDB Streams, and Datomic transaction reports show that change observation is not an exotic relational follow-up.

Where a provider supports it, the natural Genia boundary is a bounded-demand `Flow<Change>`-like source with explicit lifecycle ownership, cancellation/close behavior, provider resume position/token where applicable, and normalized Outcomes. The R32 contract must settle the exact portable change value rather than copying one provider's event shape.

### 6. Transactions are capability-specific but lifecycle-owned

R14 should own acquisition/unwind/cleanup composition. The portable contract must not equate transactions with SQL `BEGIN`/`COMMIT`.

The R32 contract should specify the smallest cross-provider atomic-work semantics it can prove and expose stronger provider semantics as capabilities. Nested transactions, savepoints, distributed transactions, and provider-specific isolation levels are not baseline assumptions.

### 7. JDBC and ODBC are adapters, not language dependencies

A JVM host/provider may use JDBC. A native host/provider may use ODBC. Another provider may use ADBC or a native client.

Changing the adapter should not require changing ordinary Genia pipeline code when the requested portable capabilities are equivalent. A C++ host must not require a JVM merely because Genia supports database connectivity.

### 8. ADBC/Arrow is especially relevant to Sheet

ADBC's columnar interchange is a strong implementation/protocol candidate for efficient Sheet sources and sinks. R32 should evaluate it explicitly.

However, Arrow record-batch size, memory layout, driver handles, and host library types must remain below the portable semantic boundary unless separately contracted.

## Proposed R32 invariant

> Genia programs interact with data stores through ordinary Genia values and existing Flow, Sheet, Outcome, configuration, secret, and lifecycle semantics. Provider selection determines storage realization and available capabilities; it does not create a second application programming model.

Provider substitution is guaranteed only for operations whose contracted capabilities and semantics match. Provider-native query text and provider-specific features are intentionally not portable.

## Proposed R32 slices

- **E32-0 — Architecture survey and contract.** Ratify the semantic matrix and define the portable/provider-specific boundary before API work.
- **E32-1 — DataStore value and capability contract.** Opaque authority-bearing value, configuration acquisition, provider identity where diagnostically necessary, capability discovery, no ambient connection state.
- **E32-2 — Stored-value mapping.** Exact scalar/nested Genia value mapping, `none`/null policy, numeric/equality/ordered-map interaction, protected-value rules, unsupported-value diagnostics.
- **E32-3 — Incremental source/read boundary.** Data-store reads as ordinary values or bounded-demand Flow with deterministic cancellation and lifecycle cleanup.
- **E32-4 — Write/mutation boundary.** Smallest truthful portable write contract plus explicit conditional/provider-specific capabilities; no fake universal CRUD.
- **E32-5 — Query boundary.** Explicit parameterized provider query capability; SQL/Datalog/Mongo/PartiQL remain provider dialects rather than Genia syntax.
- **E32-6 — Sheet integration.** Prove DataStore -> Flow<Record> -> Sheet and Sheet/Flow -> DataStore where supported; evaluate ADBC/Arrow as non-semantic optimization/interchange.
- **E32-7 — Transaction/lifecycle composition.** R14-owned acquisition/unwind with exact atomic-work and failure semantics; no universal SQL transaction assumptions.
- **E32-8 — Change-feed boundary.** Bounded-demand change Flow, cleanup/cancellation, resume metadata where supported, normalized provider failures.
- **E32-9 — Embedded relational proving provider.** SQLite proving implementation; its semantics must not leak into the portable contract.
- **E32-10 — Non-relational proving fixture.** Deterministic offline document/key-value fixture proving that core semantics do not require SQL, tables, JDBC, or network access.
- **E32-11 — External adapter boundary.** Specify JDBC/ODBC/ADBC/native adapter responsibilities without host-specific handles crossing the portable boundary.
- **E32-12 — Cross-host conformance and skeptical truth audit.** Prove provider substitution where capabilities match, bounded Flow behavior, Outcome normalization, protected configuration, lifecycle cleanup, value portability, and absence of SQL leakage.

Slice names and numbering remain planning material until the R32 contract/ticketing gate approves them.

## R32 non-goals

- ORM or active-record model
- Genia-specific SQL syntax
- universal query optimizer or query AST
- automatic translation among SQL, Datalog, Mongo aggregation, and PartiQL
- schema migration framework
- distributed transaction abstraction
- provider administration
- full production MongoDB, DynamoDB, Datomic, PostgreSQL, JDBC, ODBC, or ADBC provider matrix
- making provider-native semantics portable by assertion

## Later provider proving work

After R32 is audited, a separately gated heterogeneous-provider release should prove the contract against real, materially different stores rather than widening R32 indefinitely.

That release should include, at minimum:

1. one client/server relational provider;
2. one document or key/value provider; and
3. one provider with a change-feed capability.

MongoDB, DynamoDB, PostgreSQL through a standard adapter, ADBC, and Datomic are candidates, not commitments. Datomic is especially useful as a semantic stress test even if it remains a design/conformance reference rather than a shipped provider.

The later release must evolve providers first. Any newly discovered core semantic requirement must return to an explicit contract/design gate rather than silently redefining R32.

## Relationship to adjacent releases

R31's relational Sheet operations are useful input to R32 but do not define R32's storage model. R32 should preserve direct composition with the killer workflow while remaining neutral about relational/document/key-value/temporal realization.

R35 Portable Storage and Resource Semantics concerns Store/Location/resource addressing and should remain distinct. R32 should cross-reference R35 during contract work to avoid two competing generic "Store" concepts or duplicated authority/lifecycle mechanisms.

## Contract questions that must be settled before implementation

1. Final public abstraction name: `DataStore`, `Database`, or another non-conflicting term.
2. Exact capability representation/discovery mechanism.
3. Null/missing/`none` mapping across providers.
4. Exact source and sink operation shapes.
5. Whether a portable mutation substrate exists beyond provider capabilities.
6. Query descriptor/value shape and parameter semantics.
7. Transaction callback/scope shape and escape/lifetime rules.
8. Change event shape, ordering guarantees, resume metadata, and terminal Outcome behavior.
9. Sheet row/column mapping and duplicate/missing column rules.
10. Protected credential/configuration acquisition and authorized sink boundaries.
11. Error taxonomy and which provider details may cross the portable boundary.
12. Cross-host adapter/conformance requirements and deterministic offline fixtures.
