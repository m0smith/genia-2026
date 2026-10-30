#!/usr/bin/env bash
set -euo pipefail
cd /workspace/work/1251/main
export UV_PROJECT_ENVIRONMENT=/workspace/work/1251/docker-venv
export SSL_CERT_FILE=/run/codex-ca.pem
python --version
uv --version
clang --version
python -m uv sync --dev --python python
python -m uv run --no-sync pytest -q tests/unit/test_examples.py
cmake -S /workspace/work/1251/cpp -B /workspace/work/1251/cpp/docker-build -DCMAKE_BUILD_TYPE=Release -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
cmake --build /workspace/work/1251/cpp/docker-build -j 2
ctest --test-dir /workspace/work/1251/cpp/docker-build --output-on-failure
cd /workspace/work/1251/cpp
clang-format --dry-run --Werror src/*.cpp src/*.hpp tests/*.cpp
clang-tidy -p docker-build src/main.cpp src/adapter.hpp src/protocol.hpp
cd /workspace/work/1251/main
python -m uv run --no-sync python -m tools.spec_runner --host /workspace/work/1251/cpp/docker-build/genia-adapter --evidence /workspace/work/1251/docker-cpp-evidence.json
