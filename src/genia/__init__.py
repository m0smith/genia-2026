from .interpreter import make_global_env as make_global_env
from .interpreter import run_debug_stdio as run_debug_stdio
from .interpreter import run_source as run_source

__all__ = ["make_global_env", "run_source", "run_debug_stdio"]
