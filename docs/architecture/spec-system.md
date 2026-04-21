# Semantic Spec System

This document describes the implemented Semantic Spec System in the repository today.

## Purpose

- provide an executable shared contract surface for observable Genia behavior
- reduce drift between documentation, the Python reference host, and future host work
- keep portable contract claims smaller than the full Python implementation until shared case coverage exists

## Structure

- shared spec files currently live in `spec/eval/`
- the runner lives in `tools/spec_runner/`
- the current runner executes YAML eval cases against the Python reference host
- the current comparison surface is:
  - `stdout`
  - `stderr`
  - `exit_code`

## Contract Relationship

**LANGUAGE CONTRACT:**
- shared semantic-spec categories are `parse`, `ir`, `eval`, `cli`, `flow`, and `error`
- implemented shared case coverage currently exists for `eval` only

**PYTHON REFERENCE HOST:**
- Python is the only implemented host
- Python executes the current shared eval spec suite

## Current Limitations

- parse, ir, cli, flow, and error shared spec files are not implemented yet
- current runner normalization is limited to line-ending normalization for stdout/stderr
- no generic multi-host runner exists in this phase
