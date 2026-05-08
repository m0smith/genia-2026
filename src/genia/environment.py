"""Lexical environment and binding metadata model."""

from __future__ import annotations

import sys
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


class Env:
    def __init__(
        self,
        parent: Optional["Env"] = None,
        *,
        rebind_parent: bool | None = None,
        internal_access: bool | None = None,
    ):
        self.parent = parent
        self.values: dict[str, Any] = {}
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

    def root(self) -> "Env":
        env = self
        while env.parent is not None:
            env = env.parent
        return env

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

    def assign(self, name: str, value: Any, *, metadata: GeniaMap | None = None) -> None:
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
        GeniaFunctionGroup = _interpreter_runtime().GeniaFunctionGroup

        existing = self.values.get(fn.name)
        if existing is None:
            group = GeniaFunctionGroup(fn.name)
            if metadata is not None:
                group.merge_metadata(metadata)
            group.add_clause(fn)
            self.set(fn.name, group, assignable=True, metadata=group.metadata)
            return
        if not isinstance(existing, GeniaFunctionGroup):
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
            module_env.debug_hooks = root.debug_hooks
            module_env.debug_mode = root.debug_mode
            runtime.run_source(
                source,
                module_env,
                filename=key,
                debug_hooks=root.debug_hooks,
                debug_mode=root.debug_mode,
                internal_access=trusted,
            )
            exports = dict(module_env.values)
            module_value = ModuleValue(module_name, exports, key)
            root.loaded_modules[module_name] = module_value
            return module_value
        finally:
            root.loading_modules.remove(module_name)
