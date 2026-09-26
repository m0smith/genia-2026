# Containerized Development and Conformance Environment

Status: **development infrastructure**. This document does not define Genia
language, Core IR, host, or production deployment semantics. Implemented
language behavior remains defined by `GENIA_STATE.md`.

## Purpose

The development image gives a clean Docker-capable Linux/WSL machine one
reproducible toolchain for the current Python reference host plus the separate
`m0smith/genia-cpp` host.

It intentionally keeps source outside the image. A normal workspace is:

```text
workspace/
  genia-2026/
  genia-cpp/
```

The parent `workspace/` directory is bind-mounted at `/workspace`. The image
contains development tools only; repository-native commands still own all
build, test, lint, and conformance behavior.

## Image contents

`docker/Dockerfile.dev` currently uses:

- `python:3.14.7-trixie`, pinned by image digest
- Python 3.14.7
- `uv` 0.12.18
- Clang/clang++ 22
- clang-format 22
- clang-tidy 22
- CMake from Debian trixie
- Ninja from Debian trixie
- GNU build tools
- Git and CA certificates

Python 3.14 is the primary CI version. Genia's stable compatibility matrix is
Python 3.10 through 3.14; Python 3.15 is experimental. The container is a
single primary development environment, not a replacement for that
compatibility matrix.

The C++ host remains governed by
`docs/design/r24/dependency-toolchain-policy.md`: C++20, GCC/Clang support,
CMake, Catch2, clang-format, clang-tidy, and shared conformance from
`genia-2026`.

## Build the image

From the `genia-2026` checkout:

```bash
docker build -f docker/Dockerfile.dev -t genia-dev .
```

The root `.dockerignore` intentionally sends only the Docker definition to
the build context. Active source is never baked into the image.

## Run commands against mounted source

From `workspace/genia-2026` on Linux or WSL:

```bash
WORKSPACE="$(cd .. && pwd)"
```

Use the host UID/GID so CMake, uv, and tests do not create root-owned files in
the mounted repositories:

```bash
docker run --rm \
  --user "$(id -u):$(id -g)" \
  -v "$WORKSPACE:/workspace" \
  -w /workspace/genia-2026 \
  genia-dev \
  python --version
```

Docker Desktop users may use the same workspace layout. On Windows, running the
commands from WSL keeps path handling and UID/GID behavior closest to Linux.

## Python reference host

Bootstrap the current development dependencies:

```bash
docker run --rm \
  --user "$(id -u):$(id -g)" \
  -v "$WORKSPACE:/workspace" \
  -w /workspace/genia-2026 \
  genia-dev bash -lc \
  'python -m uv sync --dev --python python'
```

Representative Python validation:

```bash
docker run --rm \
  --user "$(id -u):$(id -g)" \
  -v "$WORKSPACE:/workspace" \
  -w /workspace/genia-2026 \
  genia-dev bash -lc \
  'python -m uv run --python python pytest -q tests/unit/test_examples.py'
```

The normal repository-wide commands remain available unchanged, including:

```bash
python -m uv run --python python ruff check .
python -m uv run --python python pytest -q -vv --maxfail=1 -m "not slow" -n auto
python -m uv run --python python python -m tools.spec_runner
```

## C++ host build and tests

Configure with the compile database needed by clang-tidy:

```bash
docker run --rm \
  --user "$(id -u):$(id -g)" \
  -v "$WORKSPACE:/workspace" \
  -w /workspace/genia-cpp \
  genia-dev bash -lc \
  'cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DCMAKE_EXPORT_COMPILE_COMMANDS=ON && cmake --build build'
```

Run CTest/Catch2:

```bash
docker run --rm \
  --user "$(id -u):$(id -g)" \
  -v "$WORKSPACE:/workspace" \
  -w /workspace/genia-cpp \
  genia-dev \
  ctest --test-dir build --output-on-failure
```

Formatting:

```bash
docker run --rm \
  --user "$(id -u):$(id -g)" \
  -v "$WORKSPACE:/workspace" \
  -w /workspace/genia-cpp \
  genia-dev bash -lc \
  'clang-format --dry-run --Werror src/*.cpp src/*.hpp tests/*.cpp'
```

Static analysis:

```bash
docker run --rm \
  --user "$(id -u):$(id -g)" \
  -v "$WORKSPACE:/workspace" \
  -w /workspace/genia-cpp \
  genia-dev \
  clang-tidy -p build src/main.cpp src/adapter.hpp src/protocol.hpp
```

## Shared conformance against C++

After the C++ build exists:

```bash
docker run --rm \
  --user "$(id -u):$(id -g)" \
  -v "$WORKSPACE:/workspace" \
  -w /workspace/genia-2026 \
  genia-dev bash -lc \
  'python -m uv run --python python python -m tools.spec_runner \
    --host /workspace/genia-cpp/build/genia-adapter \
    --evidence /tmp/genia-cpp-evidence.json'
```

The C++ repository declares the exact `genia-2026` contract revision it was
built against. If the mounted `genia-2026` checkout is newer, the runner can
report current-main compatibility but that is not the same claim as pinned
conformance. Pinned release evidence must continue to use the exact revision
declared by `genia-cpp`, as its own CI already does.

## Validation workflow

`.github/workflows/docker-dev-environment.yml` is intentionally narrow. It
builds this image on the existing Linux self-hosted runner, mounts sibling
checkouts, then runs:

1. representative Python reference-host tests
2. the real CMake configure/build path
3. CTest
4. the repository's clang-format check
5. the repository's clang-tidy check
6. the real shared conformance runner against `genia-adapter`

This workflow proves the development image only. It does not replace the
existing Python compatibility matrix or `genia-cpp`'s pinned conformance CI.

## Host parity gate

`.github/workflows/host-parity.yml` reuses this same image and `genia-cpp`
checkout/build steps for a different, narrower purpose: enforcing that a
portable-semantic change cannot silently pass in the Python reference host
while the C++ host drifts, or the reverse. It runs the "Shared conformance
against C++" command above for both hosts (producing one evidence document
each) and then runs `tools/spec_runner/host_parity_gate.py`, which compares
them against `spec/known_host_gaps.json` -- the checked-in, reasoned record
of which optional capabilities the C++ host does not yet declare
`supported`. A capability gap with no matching manifest entry, or a manifest
entry the host has since closed, fails the gate; so does any nonzero
`fail`/`protocol_error`/`crash`/`timeout`/`invalid` count in either evidence
document. To run the same check locally after building both hosts:

```bash
docker run --rm \
  --user "$(id -u):$(id -g)" \
  -v "$WORKSPACE:/workspace" \
  -w /workspace/genia-2026 \
  genia-dev bash -lc \
  'python -m uv run --python python python -m tools.spec_runner \
     --host "python -m hosts.python.protocol_adapter" \
     --evidence /tmp/python-evidence.json &&
   python -m uv run --python python python -m tools.spec_runner \
     --host /workspace/genia-cpp/build/genia-adapter \
     --evidence /tmp/cpp-evidence.json &&
   python -m uv run --python python python -m tools.spec_runner.host_parity_gate \
     --python-evidence /tmp/python-evidence.json \
     --cpp-evidence /tmp/cpp-evidence.json \
     --known-gaps spec/known_host_gaps.json'
```

This gate is CI/process infrastructure only; it defines no Genia language or
Core IR behavior, and it does not replace `.github/workflows/docker-dev-environment.yml`'s
dev-image validation above.

## Self-hosted runner implications

A future runner can reasonably move toward:

```text
host OS
  + Docker Engine
  + GitHub Actions runner
```

with Python, uv, CMake, compilers, clang-format, clang-tidy, and related build
packages supplied by `genia-dev`.

The host still needs:

- Docker Engine/daemon access
- the GitHub Actions runner and its service prerequisites
- Git/check-out support used by Actions
- enough disk for image layers, mounted source, C++ build output, and uv caches

The runner account must be authorized to access the Docker daemon. Membership
in the Docker group is effectively privileged daemon access and should be
treated accordingly.

Mounted caches are optional. If added later, prefer explicit cache directories
owned by the runner user; do not make cache layout part of Genia semantics.

For WSL, keep repository source in the Linux filesystem when practical because
bind mounts from Windows filesystems can be substantially slower for CMake and
large test trees. Nested Docker is not required when the Actions runner can
talk directly to the host Docker daemon.

## Deliberate non-goals

This environment does not add or define:

- Genia language semantics
- Core IR changes
- production runtime/container images
- Docker Compose or Kubernetes topology
- R36 execution-provider behavior
- actors, events, service discovery, or distributed placement
- image publication

Docker remains infrastructure below the Genia semantic boundary.
