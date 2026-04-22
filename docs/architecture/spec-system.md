# Semantic Spec System

This document describes the implemented Semantic Spec System in the repository today.

## Purpose

- provide an executable shared contract surface for observable Genia behavior
- reduce drift between documentation, the Python reference host, and future host work
- keep portable contract claims smaller than the full Python implementation until shared case coverage exists

## Structure

- shared spec files currently live in `spec/eval/` and `spec/ir/`
- the runner lives in `tools/spec_runner/`
- the current runner executes YAML eval and IR cases against the Python reference host
- the current comparison surface is:
  - eval: `stdout`, `stderr`, `exit_code`
  - ir: normalized portable Core IR

## Contract Relationship

**LANGUAGE CONTRACT:**
- shared semantic-spec categories are `parse`, `ir`, `eval`, `cli`, `flow`, and `error`
- implemented shared case coverage currently exists for `eval` and `ir`

**PYTHON REFERENCE HOST:**
- Python is the only implemented host
- Python executes the current shared eval and IR spec suites

## Current Limitations

- parse, cli, flow, and error shared spec files are not implemented yet
- current runner normalization is limited to line-ending normalization for eval stdout/stderr plus portable IR normalization for IR cases
- no generic multi-host runner exists in this phase
