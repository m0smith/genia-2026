"""Lexical environment and binding metadata model."""

from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

from .values import GeniaMap, ModuleValue, _merge_metadata_maps


def _interpreter_runtime() -> Any:
    for module_name in ("__main__", "genia.interpreter", "src.genia.interpreter"):
        module = sys.modules.get(module_name)
        if module is not None and hasattr(module, "run_source"):
            return module
    from . import interpreter

    return interpreter


def _check_host_visibility(visibility: str) -> None:
    """Reject an undeclared host class before installation, without rendering values."""
    if not isinstance(visibility, str) or visibility not in ("runtime-public", "entry-only"):
        raise ValueError("host visibility must be runtime-public or entry-only")


@lru_cache(maxsize=None)
def _declared_prelude_names(path: str) -> frozenset[str]:
    """Parse one autoload-target prelude file and return its top-level declared names.

    Inert: the file is parsed, never evaluated. Functions, named patterns,
    assignments and open declarations count; an annotated declaration is
    unwrapped. Cached per process because prelude sources are immutable.
    """
    from .ast_nodes import AnnotatedNode, Assign, FuncDef, NamedPatternDef, OpenFuncDef

    runtime = _interpreter_runtime()
    source, key = runtime._load_source_from_path(path)
    names: set[str] = set()
    for node in runtime.Parser(runtime.lex(source), source=source, filename=key).parse_program():
        while isinstance(node, AnnotatedNode):
            node = node.target
        if isinstance(node, (Assign, FuncDef, NamedPatternDef, OpenFuncDef)):
            names.add(node.name)
    return frozenset(names)


def runtime_owned_manifest(paths: frozenset[str]) -> frozenset[str]:
    """Return every top-level name declared by the given autoload-target prelude files.

    The static runtime-owned name manifest of contract 16.1.1 clause 3. It is
    derived from prelude source declarations, not from the autoload registry, so
    unregistered helpers such as `map_acc` are included. Packaged modules are
    never passed in and so never owned.
    """
    names: set[str] = set()
    for path in paths:
        names |= _declared_prelude_names(path)
    return frozenset(names)


def runtime_owned_manifest_paths(paths: frozenset[str], name: str) -> set[str]:
    """Return the autoload-target files that declare `name` (empty when unowned)."""
    return {path for path in paths if name in _declared_prelude_names(path)}


class Env:
    """A lexical scope: name bindings plus the module-level state of the root.

    Lookups walk `parent` links. The root environment additionally owns the
    module cache, autoload tables, and debug settings; a module's own Env owns
    its R20 contribution table (`open_contributions`). Mutated in place during
    evaluation.
    """

    # F2/P2-C topology state. Class-level defaults are immutable (None, False,
    # empty frozenset) so ordinary frames pay no per-instance cost; the owning
    # runtime scope and entry scope assign their own values on the instance.
    # `_entry` is runtime-owned registration state (None for a caller-created
    # single-root harness); `_is_entry` marks the registered entry scope E;
    # `entry_declared_runtime_owned` (E only) records the runtime-owned names the
    # entry unit itself declared (contract 16.1.4); `prelude_paths` (R only) are
    # the autoload-target prelude files captured at construction, before any host
    # pruning, so the runtime-owned manifest is never shrunk by pruning.
    _entry: "Env | None" = None
    _is_entry: bool = False
    entry_declared_runtime_owned: "set[str] | None" = None
    prelude_paths: frozenset[str] = frozenset()

    def __init__(
        self,
        parent: Optional["Env"] = None,
        *,
        rebind_parent: bool | None = None,
        internal_access: bool | None = None,
    ):
        """Create a scope under `parent` (None for a root).

        `rebind_parent` controls whether assignment may rebind a parent
        binding (default: only when a parent exists); `internal_access`
        overrides the inherited permission to see internal prelude bindings.
        """
        self.parent = parent
        # Lexical unit ownership is independent of provenance and write policy.
        # Module construction replaces this inherited reference before evaluation.
        self._unit_scope = parent.unit_scope() if parent is not None else self
        self.values: dict[str, Any] = {}
        # Host declarations are bookkeeping, separate from language metadata.
        # Both classes retain their existing placement during P1.
        self.host_binding_visibility: dict[str, str] = {}
        self.host_internal_visibility: dict[str, str] = {}
        self.host_autoload_visibility: dict[tuple[str, int], str] = {}
        self.internal_values: dict[str, Any] = {}
        self.binding_metadata: dict[str, GeniaMap] = {}
        self.assignable: set[str] = set()
        self.rebind_parent = (parent is not None) if rebind_parent is None else rebind_parent
        inherited_internal_access = parent.internal_access if parent is not None else False
        self.internal_access = inherited_internal_access if internal_access is None else internal_access
        self.autoloads: dict[tuple[str, int], str] = {}
        self.trusted_autoloads: set[tuple[str, int]] = set()
        self.loaded_files: set[str] = set()
        self.loading_files: set[str] = set()
        self.loaded_modules: dict[str, ModuleValue] = {}
        self.loading_modules: set[str] = set()
        self.debug_hooks: Any = None
        self.debug_mode: bool = False
        # R20: the canonical module/source-unit identity this environment
        # belongs to, used as half of an open interface's portable key
        # (contract §2.1). None for the entry/in-memory program environment;
        # `module_identity()` maps that to the deterministic "<entry>" id.
        self.module_id: str | None = (parent.module_id if parent is not None else None)
        # R20 contract 4.2: this module's contribution units, keyed by target
        # interface key. A table, not bindings, so units are never exports.
        self.open_contributions: dict[tuple[str, str], Any] = {}

    def module_identity(self) -> str:
        """The deterministic, portable module/source-unit identity for this
        environment (R20 contract §2.1): the canonical cached module name,
        or the fixed "<entry>" id for the top-level entry/in-memory program.
        """
        return self.module_id if self.module_id is not None else "<entry>"

    def root(self) -> "Env":
        env = self
        while env.parent is not None:
            env = env.parent
        return env

    def runtime_scope(self) -> "Env":
        """Return the existing structural root owning runtime state; never allocate."""
        return self.root()

    def entry_scope(self) -> "Env":
        """Return the execution's registered entry scope E, else the runtime root.

        A caller-created single-root harness never registers an entry, so entry
        is the root there. Evaluating source in an ordinary child does not
        register that child as entry or alter lexical parentage.
        """
        runtime = self.runtime_scope()
        return runtime._entry if runtime._entry is not None else runtime

    def unit_scope(self) -> "Env":
        """Return the declaring top-level Env inherited by lexical descendants.

        A loaded module owns itself; entry/prelude use root. The result is live
        owner identity, not a snapshot, caller scope or module-id inference.
        """
        return self._unit_scope

    def inspection_globals_scope(self) -> "Env":
        """Return the globals view for debugger/inspection consumers.

        Once an entry scope is registered the view is the declaring unit (E for
        entry frames, M for module frames, R for prelude frames). A caller-created
        single-root harness keeps the P1 compatibility view: the root.
        """
        runtime = self.runtime_scope()
        return self.unit_scope() if runtime._entry is not None else runtime

    def create_entry_scope(self) -> "Env":
        """Allocate and register the execution's entry scope E as a child of this runtime.

        Output: a new Env with parent R, parent rebinding enabled and the entry
        unit identity. After registration `entry_scope()` returns it from any Env
        of the execution. Failure: raises RuntimeError when called on a non-runtime
        Env, or when an entry scope is already registered; the first registration
        is never replaced. Side effects: marks R as sealed against late
        runtime-public host work (contract 16.1.6). PYTHON REFERENCE HOST ONLY.
        """
        if self.parent is not None:
            raise RuntimeError("entry scope registration is an operation on the runtime scope")
        if self._entry is not None:
            raise RuntimeError("entry scope is already registered for this runtime")
        entry = Env(self, rebind_parent=True)
        entry._unit_scope = entry
        entry._is_entry = True
        entry.entry_declared_runtime_owned = set()
        self._entry = entry
        return entry

    def is_runtime_owned(self, name: str) -> bool:
        """True when `name` is runtime-owned at this moment (contract 16.1.1).

        Owned means: a runtime binding or trusted internal binding, a registered
        autoload name, or any top-level declaration of an autoload-target prelude
        file (registered or not, e.g. `map_acc`). Packaged modules are not
        autoload targets and so never owned. Pure; evaluates no prelude source.
        """
        runtime = self.runtime_scope()
        if name in runtime.values or name in runtime.internal_values:
            return True
        if any(autoload_name == name for autoload_name, _arity in runtime.autoloads):
            return True
        return name in runtime_owned_manifest(runtime.prelude_paths)

    def _runtime_name_available(self, name: str) -> bool:
        """True when runtime-owned `name` can still be bound in R.

        A name that is bound, internal, autoload-registered, or declared by an
        autoload-target file that remains registered is available. A manifest
        name whose files were all pruned away by the host is not: binding it
        would recreate a denied capability (contract 16.7 MCP note).
        """
        runtime = self.runtime_scope()
        if name in runtime.values or name in runtime.internal_values:
            return True
        if any(autoload_name == name for autoload_name, _arity in runtime.autoloads):
            return True
        declaring = runtime_owned_manifest_paths(runtime.prelude_paths, name)
        return bool(declaring & set(runtime.autoloads.values()))

    def _entry_route(self, name: str) -> "Env":
        """Return the scope receiving a top-level binding operation on `name`.

        Only the registered entry scope routes: a runtime-owned name binds in R
        exactly as the single-root host did (P2 compatibility write-through, A1),
        everything else binds in E. Other scopes bind in themselves. Raises
        ValueError for a runtime-owned name that host pruning made unavailable,
        rather than recreating it in R.
        """
        if not self._is_entry or not self.is_runtime_owned(name):
            return self
        if not self._runtime_name_available(name):
            raise ValueError(f"Cannot bind {name}: the runtime name is not available in this restricted execution")
        self.entry_declared_runtime_owned.add(name)
        return self.runtime_scope()

    def binding_scope(self, name: str) -> "Env":
        """Return the scope that owns a top-level binding of `name` made from this Env."""
        return self._entry_route(name)

    def get(self, name: str) -> Any:
        env: Env | None = self
        while env is not None:
            if name in env.values:
                return env.values[name]
            env = env.parent
        root = self.root()
        if self.internal_access and name in root.internal_values:
            return root.internal_values[name]
        if root.try_autoload(name, 0) and name in root.values:
            return root.values[name]
        raise NameError(f"Undefined name: {name}")

    def set(
        self,
        name: str,
        value: Any,
        *,
        assignable: bool = True,
        metadata: GeniaMap | None = None,
        preserve_metadata: bool = False,
    ) -> None:
        """Bind `name` to `value` in this scope's own binding table.

        On the registered entry scope a runtime-owned name binds in the runtime
        scope instead (contract 16.1.2 write-through); a pruned runtime name
        raises ValueError. Metadata is replaced unless `preserve_metadata` is set.
        """
        home = self._entry_route(name)
        if home is not self:
            home.set(name, value, assignable=assignable, metadata=metadata,
                     preserve_metadata=preserve_metadata)
            return
        self.values[name] = value
        if metadata is not None:
            self.binding_metadata[name] = metadata
        elif not preserve_metadata:
            self.binding_metadata.pop(name, None)
        if assignable:
            self.assignable.add(name)
        else:
            self.assignable.discard(name)

    def set_internal(self, name: str, value: Any) -> None:
        self.root().internal_values[name] = value

    def set_host(
        self, name: str, value: Any, *, visibility: str,
        assignable: bool = True, metadata: GeniaMap | None = None,
        preserve_metadata: bool = False,
    ) -> None:
        """Classify a host injection and install it according to its class.

        Requires an explicit runtime-public or entry-only class before mutation.
        On a caller-created root with no registered entry both classes install in
        this Env (the single-root compatibility harness). Once an entry scope is
        registered an entry-only binding installs in E (from any Env of the
        execution) and a runtime-public one is rejected, because runtime work must
        finish before registration (contract 16.1.6); an entry-only injection of
        a runtime-owned name is also rejected. Classification is not language
        metadata, trust or declassification power.
        """
        _check_host_visibility(visibility)
        runtime = self.runtime_scope()
        target = self
        if runtime._entry is not None:
            if visibility == "runtime-public":
                raise ValueError("runtime-public host bindings must be installed before entry registration")
            if runtime.is_runtime_owned(name):
                raise ValueError(f"entry-only host binding cannot use the runtime-owned name {name}")
            target = runtime._entry
        target.set(name, value, assignable=assignable, metadata=metadata,
                   preserve_metadata=preserve_metadata)
        target.host_binding_visibility[name] = visibility

    def set_host_internal(self, name: str, value: Any, *, visibility: str) -> None:
        """Record a trusted internal injection on runtime, retaining its access guard.

        The class is mandatory and validated before mutation. Internal access
        remains restricted to trusted code; neither class grants that access.
        Rejected once an entry scope is registered (runtime work precedes E).
        """
        _check_host_visibility(visibility)
        if self.runtime_scope()._entry is not None:
            raise ValueError("trusted internal host bindings must be installed before entry registration")
        self.set_internal(name, value)
        self.runtime_scope().host_internal_visibility[name] = visibility

    def register_host_autoload(
        self, name: str, arity: int, path: str, *, visibility: str,
        trusted: bool = False,
    ) -> None:
        """Classify one runtime autoload key without evaluating or acquiring its file.

        Existing registration, trust and lazy loading remain unchanged. The
        declared class is recorded separately on the runtime owner. Rejected once
        an entry scope is registered, so late registration cannot turn an
        E-resident name into a runtime-owned one (contract 16.1.6).
        """
        _check_host_visibility(visibility)
        if self.runtime_scope()._entry is not None:
            raise ValueError("host autoloads must be registered before entry registration")
        self.register_autoload(name, arity, path, trusted=trusted)
        self.runtime_scope().host_autoload_visibility[(name, arity)] = visibility

    def assign(self, name: str, value: Any, *, metadata: GeniaMap | None = None) -> None:
        """Assign `value` to the nearest assignable `name`, else define it here.

        Routes like `set` on the registered entry scope. Raises NameError when the
        nearest binding is not assignable and ValueError for a pruned runtime name.
        """
        home = self._entry_route(name)
        if home is not self:
            home.assign(name, value, metadata=metadata)
            return
        target_env = self.find_assign_target(name)
        if target_env is None:
            self.set(name, value, assignable=True, metadata=metadata, preserve_metadata=metadata is None)
            return
        target_env.values[name] = value
        if metadata is not None:
            target_env.binding_metadata[name] = _merge_metadata_maps(target_env.binding_metadata.get(name), metadata)

    def find_assign_target(self, name: str) -> Optional["Env"]:
        env: Env = self
        while True:
            if name in env.values:
                if name in env.assignable:
                    return env
                raise NameError(f"Cannot assign to non-assignable name: {name}")
            if env.parent is None or not env.rebind_parent:
                return None
            env = env.parent

    def define_function(self, fn: Any, *, metadata: GeniaMap | None = None) -> None:
        """Add the named function `fn` to this scope's function group.

        Creates the group when the name is unbound, otherwise adds a clause to
        the existing group and merges `metadata`. Raises TypeError when the name
        already holds something that is not an ordinary function group: an open
        interface or linked view is named as such, anything else is reported as
        a non-function value. A duplicate arity shape is rejected by the group.
        """
        GeniaFunctionGroup = _interpreter_runtime().GeniaFunctionGroup

        home = self._entry_route(fn.name)
        if home is not self:
            home.define_function(fn, metadata=metadata)
            return
        existing = self.values.get(fn.name)
        if existing is None:
            group = GeniaFunctionGroup(fn.name)
            if metadata is not None:
                group.merge_metadata(metadata)
            group.add_clause(fn)
            self.set(fn.name, group, assignable=True, metadata=group.metadata)
            return
        if not isinstance(existing, GeniaFunctionGroup):
            from . import callable as _callable

            if isinstance(existing, (_callable.GeniaOpenFunction, _callable.GeniaLinkedOpenFunction)):
                raise TypeError(
                    f"Cannot define function {fn.name}/{fn.arity}: name is bound to an open function "
                    "interface or linked view, which an ordinary definition cannot replace"
                )
            raise TypeError(f"Cannot define function {fn.name}/{fn.arity}: name already bound to non-function value")
        if metadata is not None:
            existing.merge_metadata(metadata)
            self.binding_metadata[fn.name] = existing.metadata
        existing.add_clause(fn)

    def get_metadata(self, name: str) -> GeniaMap:
        if name in self.values:
            return self.binding_metadata.get(name, GeniaMap())
        if self.parent is not None:
            return self.parent.get_metadata(name)
        raise NameError(f"Undefined name: {name}")

    def merge_binding_metadata(self, name: str, metadata: GeniaMap) -> None:
        GeniaFunctionGroup = _interpreter_runtime().GeniaFunctionGroup

        env: Env = self
        while True:
            if name in env.values:
                merged = _merge_metadata_maps(env.binding_metadata.get(name), metadata)
                env.binding_metadata[name] = merged
                value = env.values[name]
                if isinstance(value, GeniaFunctionGroup):
                    value.metadata = merged
                return
            if env.parent is None:
                raise NameError(f"Undefined name: {name}")
            env = env.parent

    def register_autoload(self, name: str, arity: int, path: str, *, trusted: bool = False) -> None:
        root = self.root()
        key = (name, arity)
        root.autoloads[key] = path
        if trusted:
            root.trusted_autoloads.add(key)
        else:
            root.trusted_autoloads.discard(key)

    def try_autoload(self, name: str, arity: int) -> bool:
        runtime = _interpreter_runtime()

        root = self.root()
        autoload_key = (name, arity)
        path = root.autoloads.get(autoload_key)
        if path is None:
            for candidate_key, candidate_path in root.autoloads.items():
                autoload_name, _ = candidate_key
                if autoload_name == name:
                    autoload_key = candidate_key
                    path = candidate_path
                    break
            if path is None:
                return False

        source, key = runtime._load_source_from_path(path)

        if key in root.loaded_files:
            return True

        if key in root.loading_files:
            raise RuntimeError(f"Autoload cycle detected while loading {key}")

        root.loading_files.add(key)
        try:
            runtime.run_source(
                source,
                root,
                filename=key,
                debug_hooks=root.debug_hooks,
                debug_mode=root.debug_mode,
                internal_access=autoload_key in root.trusted_autoloads,
            )
            root.loaded_files.add(key)
            return True
        finally:
            root.loading_files.remove(key)

    def resolve_module_source(self, module_name: str, requester_filename: str | None = None) -> tuple[str, str, bool]:
        runtime = _interpreter_runtime()

        candidates: list[Path] = []
        if requester_filename and requester_filename not in {"<memory>", "<command>"}:
            requester = Path(requester_filename)
            candidates.append((requester.parent / f"{module_name}.genia").resolve())
        candidates.append((runtime.BASE_DIR / f"{module_name}.genia").resolve())
        for path in candidates:
            if path.is_file():
                return path.read_text(encoding="utf-8"), str(path), False
        packaged = runtime._resolve_packaged_module(module_name)
        if packaged is not None:
            source, key = packaged
            return source, key, True
        raise FileNotFoundError(f"Module not found: {module_name}")

    def load_module(self, module_name: str, requester_filename: str | None = None) -> ModuleValue:
        """Load and cache the module `module_name`, returning its ModuleValue.

        Output: a cached value when already loaded; otherwise the module's
        source is resolved (relative to `requester_filename`, the base
        directory, then packaged modules), run once in its own Env under the
        root, and its top-level bindings become the exports. Its R20
        contribution table is copied onto the value but is never an export.
        Failure: raises on an import cycle or a module that cannot be found.
        Side effects: executes the module's top-level code once per root.
        """
        runtime = _interpreter_runtime()

        root = self.root()
        if module_name in root.loaded_modules:
            return root.loaded_modules[module_name]
        if module_name in root.loading_modules:
            raise RuntimeError(f"Module import cycle detected while loading {module_name}")
        if module_name == "python" or module_name.startswith("python."):
            module_value = runtime._build_python_host_module(root, module_name)
            root.loaded_modules[module_name] = module_value
            return module_value

        source, key, trusted = root.resolve_module_source(module_name, requester_filename)
        root.loading_modules.add(module_name)
        try:
            module_env = Env(root, rebind_parent=False)
            module_env._unit_scope = module_env
            module_env.debug_hooks = root.debug_hooks
            module_env.debug_mode = root.debug_mode
            # R20: canonical module identity is the requested/cached module
            # name — the same key `loaded_modules` is keyed by — never the
            # import alias or resolved filesystem path (contract §2.1).
            module_env.module_id = module_name
            runtime.run_source(
                source,
                module_env,
                filename=key,
                debug_hooks=root.debug_hooks,
                debug_mode=root.debug_mode,
                internal_access=trusted,
            )
            exports = dict(module_env.values)
            module_value = ModuleValue(module_name, exports, key, dict(module_env.open_contributions))
            root.loaded_modules[module_name] = module_value
            return module_value
        finally:
            root.loading_modules.remove(module_name)
