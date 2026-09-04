# Function Reference

Alphabetical index of the **286** out-of-the-box Genia functions available from the autoloaded prelude and Python reference host. Every entry is generated from canonical documentation metadata -- see [the @doc Style Guide](../style/doc-style.md). Do not edit these pages by hand.

## All functions (A-Z)

| Function | Category | Signature | Summary |
| --- | --- | --- | --- |
| [`abs`](functions/abs.md) | math | `abs(x)` | Return the absolute value of a number. |
| [`absence_context`](functions/absence_context.md) | option | `absence_context(opt)` | Read the optional context metadata of a structured `none(...)` value. |
| [`absence_meta`](functions/absence_meta.md) | option | `absence_meta(opt)` | Read the full metadata of a structured `none(...)` value as a map. |
| [`absence_reason`](functions/absence_reason.md) | option | `absence_reason(opt)` | Read the reason label of a structured `none(...)` value. |
| [`actor`](functions/actor.md) | actor | `actor(initial_state, handler)` | Create an actor with initial state and a message handler. |
| [`actor_alive?`](functions/actor_alive-p.md) | actor | `actor_alive?(a)` | Check whether an actor's worker thread is alive. |
| [`actor_call`](functions/actor_call.md) | actor | `actor_call(a, msg)` | Send a message and wait for a reply (synchronous request-reply). |
| [`actor_error`](functions/actor_error.md) | actor | `actor_error(a)` | Return the actor error option. |
| [`actor_failed?`](functions/actor_failed-p.md) | actor | `actor_failed?(a)` | Check whether an actor has failed. |
| [`actor_restart`](functions/actor_restart.md) | actor | `actor_restart(a, new_state)` | Restart a failed or stopped actor with a new initial state. |
| [`actor_send`](functions/actor_send.md) | actor | `actor_send(a, msg)` | Send a message to an actor for asynchronous processing. |
| [`actor_state`](functions/actor_state.md) | actor | `actor_state(a)` | Read the current actor state without sending a message. |
| [`actor_status`](functions/actor_status.md) | actor | `actor_status(a)` | Return the actor status string. |
| [`actor_stop`](functions/actor_stop.md) | actor | `actor_stop(a)` | Gracefully stop an actor after draining its mailbox. |
| [`any?`](functions/any-p.md) | list | `any?(predicate, xs)` | Return `true` when any element satisfies a predicate. |
| [`append`](functions/append.md) | list | `append()` | Concatenate zero or more lists. |
| [`application_expr?`](functions/application_expr-p.md) | syntax | `application_expr?(expr)` | Check whether `expr` is a quoted application form `(app operator operand1 operand2 ...)`. |
| [`apply`](functions/apply.md) | fn | `apply(proc, args)` | Call `proc` with a list of positional arguments. |
| [`apply_raw`](functions/apply_raw.md) | Function helpers | `apply_raw(function, arguments)` | Call a function with a list of positional arguments without automatic absence propagation. |
| [`argv`](functions/argv.md) | CLI | `argv()` | Return the trailing command-line arguments as a list of strings. |
| [`as_seq`](functions/as_seq.md) | flow | `as_seq(value)` | Explicitly adapt a list or string into a Seq-compatible ordered source. |
| [`assert_eq`](functions/assert_eq.md) | Testing | `assert_eq(actual, expected)` | Assert that two values are equal. |
| [`assert_true`](functions/assert_true.md) | Testing | `assert_true(value)` | Assert that a value is true. |
| [`assignment_expr?`](functions/assignment_expr-p.md) | syntax | `assignment_expr?(expr)` | Check whether `expr` is an assignment form `(assign name value)`. |
| [`assignment_name`](functions/assignment_name.md) | syntax | `assignment_name(expr)` | Return the assigned symbol from a quoted assignment expression. |
| [`assignment_value`](functions/assignment_value.md) | syntax | `assignment_value(expr)` | Return the value expression from a quoted assignment expression. |
| [`awk_count`](functions/awk_count.md) | awk | `awk_count(predicate, xs)` | Count rows that satisfy an AWK-style predicate. |
| [`awk_filter`](functions/awk_filter.md) | awk | `awk_filter(predicate, xs)` | Filter rows with an AWK-style predicate. |
| [`awk_map`](functions/awk_map.md) | awk | `awk_map(fn, xs)` | Map rows with AWK-style line numbering. |
| [`awkify`](functions/awkify.md) | awk | `awkify(fn, xs)` | Apply an AWK-style row function over a list of rows. |
| [`block_expr?`](functions/block_expr-p.md) | syntax | `block_expr?(expr)` | Check whether `expr` is a block form `(block ...)`. |
| [`block_expressions`](functions/block_expressions.md) | syntax | `block_expressions(expr)` | Return the tail of a quoted block expression as a pair-chain sequence of subexpressions. |
| [`branch_body`](functions/branch_body.md) | syntax | `branch_body(branch)` | Return the quoted result/body expression of a match branch. |
| [`branch_guard`](functions/branch_guard.md) | syntax | `branch_guard(branch)` | Return the quoted guard of a guarded match branch. |
| [`branch_has_guard?`](functions/branch_has_guard-p.md) | syntax | `branch_has_guard?(branch)` | Check whether a quoted match branch carries a guard expression. |
| [`branch_pattern`](functions/branch_pattern.md) | syntax | `branch_pattern(branch)` | Return the quoted pattern of a match branch. |
| [`byte_length`](functions/byte_length.md) | string | `byte_length(value)` | Return the UTF-8 byte length of a string. |
| [`car`](functions/car.md) | Pairs | `car(pair)` | Return the first value of a pair. |
| [`cdr`](functions/cdr.md) | Pairs | `cdr(pair)` | Return the second value of a pair. |
| [`cell`](functions/cell.md) | cell | `cell(initial)` | Create a ready cell with initial state and no cached error. |
| [`cell_alive?`](functions/cell_alive-p.md) | cell | `cell_alive?(cell)` | Check whether the cell worker thread is alive. |
| [`cell_error`](functions/cell_error.md) | cell | `cell_error(cell)` | Return `none` when the cell is ready, or `some(error)` when failed. |
| [`cell_failed?`](functions/cell_failed-p.md) | cell | `cell_failed?(cell)` | Check whether a cell is currently failed. |
| [`cell_get`](functions/cell_get.md) | cell | `cell_get(cell)` | Read the current cell state. |
| [`cell_send`](functions/cell_send.md) | cell | `cell_send(cell, update)` | Queue an asynchronous state update function for a cell. |
| [`cell_state`](functions/cell_state.md) | cell | `cell_state(cell)` | Alias for `cell_get`. |
| [`cell_status`](functions/cell_status.md) | cell | `cell_status(cell)` | Return `"ready"` or `"failed"`. |
| [`cell_stop`](functions/cell_stop.md) | cell | `cell_stop(cell)` | Gracefully stop a cell after draining its mailbox. |
| [`cell_with_state`](functions/cell_with_state.md) | cell | `cell_with_state(state)` | Create a ready cell backed by the provided ref. |
| [`chunk`](functions/chunk.md) | Retrieval | `chunk(chunker, document)` | Construct exact ordered chunks from a validated document and chunker callback. |
| [`clear_screen`](functions/clear_screen.md) | io | `clear_screen()` | Clear the terminal screen and move the cursor to the top-left corner. |
| [`cli_flag?`](functions/cli_flag-p.md) | cli | `cli_flag?(opts, name)` | Check whether parsed options contain a truthy flag value. |
| [`cli_option`](functions/cli_option.md) | cli | `cli_option(opts, name)` | Return a parsed option value when present. |
| [`cli_option_or`](functions/cli_option_or.md) | cli | `cli_option_or(opts, name, default)` | Return a parsed option value or `default` when the option is missing. |
| [`cli_parse`](functions/cli_parse.md) | cli | `cli_parse(args)` | Parse raw CLI args into `[opts, positionals]`, optionally using a minimal `flags` / `options` / `aliases` spec map. |
| [`collect`](functions/collect.md) | flow | `collect(source)` | Return list data from a list or by materializing a Flow. |
| [`collect_sheet`](functions/collect_sheet.md) | Sheets | `collect_sheet(records)` | Collect homogeneous map records into an immutable Sheet. |
| [`collect_validated`](functions/collect_validated.md) | Validation | `collect_validated(results)` | Collect Outcome values into clean values and diagnostics. |
| [`columns`](functions/columns.md) | Sheets | `columns(sheet)` | Return a Sheet's column names in deterministic order. |
| [`compose`](functions/compose.md) | fn | `compose(..fns)` | Compose functions right-to-left into one callable. |
| [`concat`](functions/concat.md) | string | `concat(left, right)` | Concatenate two strings. |
| [`config_args`](functions/config_args.md) | Configuration | `config_args(arguments)` | Normalize explicit program arguments into an R10 values-source descriptor. |
| [`config_get`](functions/config_get.md) | Configuration | `config_get(provider, key)` | Read and validate one configuration value through a provider. |
| [`config_get_or`](functions/config_get_or.md) | Configuration | `config_get_or(provider, key, default)` | Read and validate one configuration value or use an explicit default. |
| [`config_provider`](functions/config_provider.md) | Configuration | `config_provider(source)` | Construct an ordinary configuration provider from an explicit source. |
| [`config_standard`](functions/config_standard.md) | Configuration | `config_standard(overrides, arguments)` | Construct the conventional ordered configuration provider snapshot. |
| [`config_view`](functions/config_view.md) | Configuration | `config_view(provider, prefix)` | Construct a qualified configuration lookup callable over an explicit provider. |
| [`cons`](functions/cons.md) | Pairs | `cons(first, second)` | Construct a pair from two values. |
| [`contains`](functions/contains.md) | string | `contains(haystack, needle)` | Check whether `needle` occurs inside `haystack`. |
| [`count`](functions/count.md) | list | `count(xs)` | Count elements in a list. |
| [`debug_repr`](functions/debug_repr.md) | I/O | `debug_repr(value)` | Return the deterministic debug representation of a value. |
| [`dec`](functions/dec.md) | math | `dec(x)` | Decrement a number by one. |
| [`declassify`](functions/declassify.md) | Configuration | `declassify(authority, value)` | Declassify a protected value with matching explicit authority. |
| [`define`](functions/define.md) | eval | `define(env, name, value)` | Define a name in the current metacircular environment frame. |
| [`derive`](functions/derive.md) | Sheets | `derive(sheet, column, function)` | Return a Sheet with one derived column. |
| [`diagnostic_error`](functions/diagnostic_error.md) | validation | `diagnostic_error(index, field, reason, context)` | Create a field/index-aware error diagnostic map. |
| [`diagnostic_field`](functions/diagnostic_field.md) | validation | `diagnostic_field(diagnostic)` | Return a diagnostic map's field. |
| [`diagnostic_reason`](functions/diagnostic_reason.md) | validation | `diagnostic_reason(diagnostic)` | Return a diagnostic map's reason. |
| [`diagnostic_skipped`](functions/diagnostic_skipped.md) | validation | `diagnostic_skipped(index, field, reason, context)` | Create a field/index-aware skipped diagnostic map. |
| [`display`](functions/display.md) | I/O | `display(value)` | Return the display representation of a value. |
| [`doc`](functions/doc.md) | Documentation | `doc(name)` | Return the canonical documentation string for a bound name. |
| [`drop`](functions/drop.md) | list | `drop(n, xs)` | Drop the first `n` items from a list. |
| [`each`](functions/each.md) | flow | `each(fn, source)` | Run `fn` for each item of a list or Flow, passing the original items through. |
| [`embed`](functions/embed.md) | Retrieval | `embed(provider, config, credential, authority)` | Construct an embedding callable through an explicit provider boundary. |
| [`empty?`](functions/empty-p.md) | list | `empty?(xs)` | Check whether a list has no elements. |
| [`empty_env`](functions/empty_env.md) | eval | `empty_env()` | Create a fresh metacircular evaluation environment. |
| [`ends_with`](functions/ends_with.md) | string | `ends_with(value, suffix)` | Check whether a string ends with a suffix. |
| [`entry_bytes`](functions/entry_bytes.md) | File / zip | `entry_bytes(entry)` | Return the bytes stored in a zip entry. |
| [`entry_json`](functions/entry_json.md) | File / zip | `entry_json(entry)` | Return whether a zip entry name has a JSON suffix. |
| [`entry_name`](functions/entry_name.md) | File / zip | `entry_name(entry)` | Return a zip entry's filename. |
| [`err`](functions/err.md) | option | `err(..args)` | Construct a recoverable Outcome failure value `err(reason)`. |
| [`eval`](functions/eval.md) | eval | `eval(expr, env)` | Evaluate a quoted Genia expression in a metacircular environment. |
| [`evolve`](functions/evolve.md) | flow | `evolve(init, step)` | Create a Flow by repeatedly applying `step` to the previous value. |
| [`exact_shape_match`](functions/exact_shape_match.md) | Value templates | `exact_shape_match(shape, value)` | Match a value against an exact shape template. |
| [`extend`](functions/extend.md) | eval | `extend(env, params, args)` | Create a child metacircular environment with lambda parameters bound to argument values. |
| [`fields`](functions/fields.md) | awk | `fields(row)` | Split a row into whitespace-separated fields, keeping the original row first. |
| [`filter`](functions/filter.md) | list | `filter(predicate, xs)` | Keep elements where `predicate(x)` is `true`. |
| [`find`](functions/find.md) | string | `find(value, needle)` | Find the first index of `needle` within `value`. |
| [`find_opt`](functions/find_opt.md) | list | `find_opt(predicate, xs)` | Canonical maybe-returning predicate-search helper for lists. |
| [`first`](functions/first.md) | list | `first(xs)` | Return the first element as structured absence-aware Option. |
| [`first_opt`](functions/first_opt.md) | list | `first_opt(xs)` | Compatibility alias for `first(list)`. |
| [`flat_map_some`](functions/flat_map_some.md) | option | `flat_map_some(f, opt)` | Apply the Option-returning function `f` to the inner value of `some(value)`. |
| [`flush`](functions/flush.md) | io | `flush(sink)` | Flush an output sink. |
| [`force`](functions/force.md) | Evaluation | `force(promise)` | Force a delayed promise and return its value. |
| [`format`](functions/format.md) | string | `format(template, values)` | Render `template` by substituting placeholders from `values`. |
| [`Format`](functions/Format-host.md) | Value templates | `Format(template, tag)` | Construct a tagged representation template. |
| [`format_compose`](functions/format_compose.md) | string | `format_compose(parts)` | Compose string templates and Format values into one reusable Format. |
| [`format_tag`](functions/format_tag.md) | Value templates | `format_tag(format)` | Return the tag of a representation template. |
| [`format_template`](functions/format_template.md) | Value templates | `format_template(format)` | Return the inner template of a representation template. |
| [`get`](functions/get.md) | option | `get(key, target)` | Look up `key` in a map target, returning an absence-aware Option. |
| [`get?`](functions/get-p.md) | option | `get?(key, target)` | Compatibility alias for `get(key, target)`. |
| [`head`](functions/head.md) | list | `head(xs)` | Convenience alias for `take`. |
| [`help`](functions/help.md) | Documentation | `help()` | Show the public help overview or documentation for one bound name. |
| [`inc`](functions/inc.md) | math | `inc(x)` | Increment a number by one. |
| [`index`](functions/index.md) | Retrieval | `index(provider, config, credential, authority)` | Construct an opaque retrieval index through an explicit provider boundary. |
| [`input`](functions/input.md) | I/O | `input()` | Read one line from standard input. |
| [`inspect`](functions/inspect.md) | fn | `inspect(value)` | Log `value` for debugging and return it unchanged. |
| [`is_empty`](functions/is_empty.md) | string | `is_empty(value)` | Check whether a string is empty. |
| [`is_none?`](functions/is_none-p.md) | option | `is_none?(opt)` | Alias for `none?(opt)`. |
| [`is_some?`](functions/is_some-p.md) | option | `is_some?(opt)` | Alias for `some?(opt)`. |
| [`join`](functions/join.md) | string | `join(sep, xs)` | Join the strings in `xs` with `sep` between elements. |
| [`json_decode`](functions/json_decode.md) | json | `json_decode(value)` | Decode JSON text or UTF-8 bytes through the portable JSON representation boundary. |
| [`json_encode`](functions/json_encode.md) | json | `json_encode(value)` | Encode a supported ordinary or `json`-represented value as deterministic JSON. |
| [`json_parse`](functions/json_parse.md) | json | `json_parse(value)` | Parse JSON text into Genia runtime data. |
| [`json_pretty`](functions/json_pretty.md) | json | `json_pretty(value)` | Compatibility alias for `json_stringify`. |
| [`json_schema`](functions/json_schema.md) | json | `json_schema(schema)` | Compile the supported JSON Schema structural subset into a Template. |
| [`json_stringify`](functions/json_stringify.md) | json | `json_stringify(value)` | Render a Genia value as deterministic pretty JSON. |
| [`keep_some`](functions/keep_some.md) | flow | `keep_some(flow)` | Keep only successful Option values from a flow. |
| [`keep_some_else`](functions/keep_some_else.md) | flow | `keep_some_else(stage, dead_handler)` | Apply an Option-returning `stage` to each flow item, routing failures to `dead_handler`. |
| [`lambda_body`](functions/lambda_body.md) | syntax | `lambda_body(expr)` | Return the quoted lambda body. |
| [`lambda_expr?`](functions/lambda_expr-p.md) | syntax | `lambda_expr?(expr)` | Check whether `expr` is a lambda form. |
| [`lambda_params`](functions/lambda_params.md) | syntax | `lambda_params(expr)` | Return the quoted lambda parameter structure. |
| [`last`](functions/last.md) | list | `last(xs)` | Return the last element as an Option. |
| [`length`](functions/length.md) | list | `length(xs)` | Count elements in a list. |
| [`lifecycle_child`](functions/lifecycle_child.md) | Lifecycle | `lifecycle_child(scope_handle, peers, work)` | Run a child execution scope nested under an active parent scope handle. |
| [`lifecycle_context`](functions/lifecycle_context.md) | Lifecycle | `lifecycle_context(scope_handle, name)` | Read inward-only lifecycle context exposed by an entered peer or an ancestor scope. |
| [`lifecycle_repeat`](functions/lifecycle_repeat.md) | Lifecycle | `lifecycle_repeat(peers, source, element_work)` | Run a fresh element execution scope for each consumed list or flow element, exposing reserved element/index context. |
| [`lifecycle_scope`](functions/lifecycle_scope.md) | Lifecycle | `lifecycle_scope(peers, work)` | Run a fresh root execution scope through explicit peer definitions and one work callable. |
| [`lines`](functions/lines.md) | flow | `lines(source)` | Create a Flow from `stdin`, an incoming Flow, or a list of strings. |
| [`list`](functions/list.md) | list | `list(..xs)` | Build a list from all provided arguments. |
| [`log`](functions/log.md) | I/O | `log(..values)` | Write values to standard error with a trailing newline. |
| [`lookup`](functions/lookup.md) | eval | `lookup(env, name)` | Look up a symbol in a metacircular evaluation environment. |
| [`lower`](functions/lower.md) | string | `lower(value)` | Convert a string to lowercase. |
| [`map`](functions/map.md) | list | `map(f, xs)` | Apply a function to every list element. |
| [`map_count`](functions/map_count.md) | map | `map_count(map)` | Return the number of entries in a map. |
| [`map_get`](functions/map_get.md) | map | `map_get(map, key)` | Return the stored value for `key`, or `none("missing-key", {key: key})` when absent. |
| [`map_has?`](functions/map_has-p.md) | map | `map_has?(map, key)` | Report whether a map contains `key`. |
| [`map_item_key`](functions/map_item_key.md) | map | `map_item_key(mi)` | Return the key from a map item `[key, value]` pair. |
| [`map_item_value`](functions/map_item_value.md) | map | `map_item_value(mi)` | Return the value from a map item `[key, value]` pair. |
| [`map_items`](functions/map_items.md) | map | `map_items(map)` | Return the entries of a map as a list of `[key, value]` pairs. |
| [`map_keys`](functions/map_keys.md) | map | `map_keys(m)` | Return a list of all keys in a map. |
| [`map_new`](functions/map_new.md) | map | `map_new(..xs)` | Create an empty persistent map value. |
| [`map_put`](functions/map_put.md) | map | `map_put(map, key, value)` | Return a new map with `key` set to `value`. |
| [`map_remove`](functions/map_remove.md) | map | `map_remove(map, key)` | Return a new map with `key` removed. |
| [`map_some`](functions/map_some.md) | option | `map_some(f, opt)` | Apply `f` to the inner value of `some(value)`, returning `some(result)`. |
| [`map_values`](functions/map_values.md) | map | `map_values(m)` | Return a list of all values in a map. |
| [`match_branches`](functions/match_branches.md) | syntax | `match_branches(expr)` | Return the quoted branch sequence of a match expression. |
| [`match_expr?`](functions/match_expr-p.md) | syntax | `match_expr?(expr)` | Check whether `expr` is a quoted pattern-match form `(match ...)`. |
| [`max`](functions/max.md) | math | `max(a, b)` | Return the larger of two numbers. |
| [`merge`](functions/merge.md) | flow | `merge(pair)` | Concatenate two flows into one output flow. |
| [`meta`](functions/meta.md) | Documentation | `meta(name)` | Return the metadata map for a bound name. |
| [`min`](functions/min.md) | math | `min(a, b)` | Return the smaller of two numbers. |
| [`mod`](functions/mod.md) | math | `mod(a, b)` | Return the remainder of `a / b`. |
| [`model`](functions/model.md) | AI composition | `model(provider, config, credential, authority)` | Construct a model callable through an explicit provider boundary. |
| [`move_cursor`](functions/move_cursor.md) | io | `move_cursor(x, y)` | Move the terminal cursor to column `x`, row `y`. |
| [`nil?`](functions/nil-p.md) | list | `nil?(x)` | Check whether a value is `nil`. |
| [`none?`](functions/none-p.md) | option | `none?(value)` | Check whether a value is any `none...` Option form. |
| [`nth`](functions/nth.md) | list | `nth(n, xs)` | Return the element at zero-based index `n` as structured absence-aware Option. |
| [`nth_opt`](functions/nth_opt.md) | list | `nth_opt(n, xs)` | Compatibility alias for `nth(index, list)`. |
| [`null?`](functions/null-p.md) | Pairs | `null?(value)` | Return whether a value is the empty pair-list terminator. |
| [`open_shape_match`](functions/open_shape_match.md) | Value templates | `open_shape_match(shape, value)` | Match a value against an open shape template. |
| [`operands`](functions/operands.md) | syntax | `operands(expr)` | Return the operand tail of a quoted application expression as a pair-chain sequence. |
| [`operator`](functions/operator.md) | syntax | `operator(expr)` | Return the operator/callee part of a quoted application expression. |
| [`or_else`](functions/or_else.md) | option | `or_else(opt, fallback)` | Unwrap `some(...)`, falling back to `fallback` for `none(...)`. |
| [`or_else_with`](functions/or_else_with.md) | option | `or_else_with(opt, thunk)` | Unwrap `some(...)`, calling `thunk()` for `none(...)`. |
| [`pair?`](functions/pair-p.md) | Pairs | `pair?(value)` | Return whether a value is a pair. |
| [`pairs`](functions/pairs.md) | map | `pairs(xs, ys)` | Zip two lists into a list of `[x, y]` pairs, bounded by the shorter input. |
| [`parse_csv_row`](functions/parse_csv_row.md) | json | `parse_csv_row(line)` | Parse one CSV row into an Outcome. |
| [`parse_int`](functions/parse_int.md) | string | `parse_int(value)` | Parse an integer from a string, with optional explicit base. |
| [`parse_jsonl_record`](functions/parse_jsonl_record.md) | json | `parse_jsonl_record(line)` | Parse one JSONL object record into an Outcome. |
| [`print`](functions/print.md) | I/O | `print(..values)` | Write values to standard output with a trailing newline. |
| [`process_alive?`](functions/process_alive-p.md) | process | `process_alive?(process)` | Check whether a process worker is still alive. |
| [`protected_match`](functions/protected_match.md) | Configuration | `protected_match(template, value)` | Match a value while preserving the protected carrier boundary. |
| [`quasiquoted_expr?`](functions/quasiquoted_expr-p.md) | syntax | `quasiquoted_expr?(expr)` | Check whether `expr` is a quasiquoted form `(quasiquote ...)`. |
| [`quoted_expr?`](functions/quoted_expr-p.md) | syntax | `quoted_expr?(expr)` | Check whether `expr` is a quoted form `(quote ...)`. |
| [`rand`](functions/rand.md) | random | `rand()` | Advance an explicit RNG state and return `[next_rng_state, float]`. |
| [`rand_flow`](functions/rand_flow.md) | random | `rand_flow(seed)` | Return a lazy seeded Flow of floats in `[0, 1)`. |
| [`rand_int`](functions/rand_int.md) | random | `rand_int(n)` | Advance an explicit RNG state and return `[next_rng_state, int]`. |
| [`rand_int_flow`](functions/rand_int_flow.md) | random | `rand_int_flow(seed, n)` | Return a lazy seeded Flow of integers in `[0, n)`. |
| [`range`](functions/range.md) | list | `range(stop)` | Build a numeric range. |
| [`read_file`](functions/read_file.md) | file | `read_file(path)` | Read a UTF-8 text file from `path`. |
| [`reduce`](functions/reduce.md) | list | `reduce(f, acc, xs)` | Fold a list from left to right. |
| [`ref`](functions/ref.md) | ref | `ref()` | Create a synchronized ref, optionally with an initial value. |
| [`ref_get`](functions/ref_get.md) | ref | `ref_get(ref_value)` | Read the current value from a ref. |
| [`ref_is_set`](functions/ref_is_set.md) | ref | `ref_is_set(ref_value)` | Check whether a ref currently holds a value. |
| [`ref_set`](functions/ref_set.md) | ref | `ref_set(ref_value, value)` | Set a ref to `value` and return `value`. |
| [`ref_update`](functions/ref_update.md) | ref | `ref_update(ref_value, updater)` | Apply `updater` to the current ref value atomically and store the result. |
| [`refine`](functions/refine.md) | flow | `refine(..steps)` | Apply step functions left-to-right to each incoming flow item. |
| [`refinement_match`](functions/refinement_match.md) | Value templates | `refinement_match(template, value)` | Match a value against a refinement template. |
| [`render_csv`](functions/render_csv.md) | Sheets | `render_csv(sheet)` | Render an immutable Sheet as deterministic CSV text. |
| [`render_grid`](functions/render_grid.md) | io | `render_grid(grid)` | Render a simple text grid to stdout. |
| [`represent`](functions/represent.md) | Value templates | `represent(format, value)` | Attach a first-class representation facet to a value. |
| [`representation_match`](functions/representation_match.md) | Value templates | `representation_match(template, value)` | Match a represented value against a representation template. |
| [`rerank`](functions/rerank.md) | Retrieval | `rerank(provider, config, credential, authority)` | Construct a provenance-preserving reranker through an explicit provider boundary. |
| [`rest`](functions/rest.md) | list | `rest(xs)` | Return all elements except the first. |
| [`restart_cell`](functions/restart_cell.md) | cell | `restart_cell(cell, new_state)` | Replace the cell state, clear cached failure, and mark the cell ready again. |
| [`retrieve`](functions/retrieve.md) | Retrieval | `retrieve(provider, config, credential, authority)` | Construct a retrieval callable through an explicit provider boundary. |
| [`reverse`](functions/reverse.md) | list | `reverse(xs)` | Return a list with elements in reverse order. |
| [`rng`](functions/rng.md) | random | `rng(seed)` | Create an explicit deterministic RNG state from `seed`. |
| [`row_get`](functions/row_get.md) | Sheets | `row_get(row, column)` | Read one named value from a Sheet row representation. |
| [`rows`](functions/rows.md) | Sheets | `rows(sheet)` | Return a Sheet's rows as ordered name/value pairs. |
| [`rule_ctx`](functions/rule_ctx.md) | flow | `rule_ctx(ctx)` | Replace the running `ctx` for later `rules(..fns)` rules and later input items. |
| [`rule_emit`](functions/rule_emit.md) | flow | `rule_emit(x)` | Emit one output value from a `rules(..fns)` rule. |
| [`rule_emit_many`](functions/rule_emit_many.md) | flow | `rule_emit_many(xs)` | Emit a list of output values from a `rules(..fns)` rule. |
| [`rule_halt`](functions/rule_halt.md) | flow | `rule_halt()` | Stop later `rules(..fns)` rules for the current input item. |
| [`rule_set`](functions/rule_set.md) | flow | `rule_set(record)` | Replace the current record for later `rules(..fns)` rules on the same input item. |
| [`rule_skip`](functions/rule_skip.md) | flow | `rule_skip()` | Return `none` for a `rules(..fns)` rule with no effect. |
| [`rule_step`](functions/rule_step.md) | flow | `rule_step(record, ctx, out)` | Replace `record`, replace `ctx`, and emit `out` in one `rules(..fns)` step. |
| [`rules`](functions/rules.md) | flow | `rules(..fns)` | Apply rule functions left-to-right to each incoming flow item. |
| [`run`](functions/run.md) | flow | `run(source)` | Consume or traverse a list or Flow to completion and return nil. |
| [`scan`](functions/scan.md) | flow | `scan(step, initial_state)` | Stateful flow transform driven by `step`. |
| [`secret_get`](functions/secret_get.md) | Configuration | `secret_get(provider, key, authority)` | Read and validate one protected secret through a provider. |
| [`secret_get_or`](functions/secret_get_or.md) | Configuration | `secret_get_or(provider, key, default, authority)` | Read and validate one protected secret or use an explicit protected default. |
| [`secret_view`](functions/secret_view.md) | Configuration | `secret_view(provider, prefix, purpose)` | Construct a qualified protected-secret lookup callable over an explicit provider. |
| [`select`](functions/select.md) | Sheets | `select(sheet, columns)` | Return a Sheet containing selected columns. |
| [`self_evaluating?`](functions/self_evaluating-p.md) | syntax | `self_evaluating?(expr)` | Check whether a quoted expression is self-evaluating. |
| [`send`](functions/send.md) | process | `send(process, message)` | Enqueue `message` for a process mailbox. |
| [`set`](functions/set.md) | eval | `set(env, name, value)` | Rebind the nearest existing lexical name in a metacircular environment chain, or define it in the current frame when missing. |
| [`set_entry_bytes`](functions/set_entry_bytes.md) | File / zip | `set_entry_bytes(entry, bytes)` | Return a zip entry with replacement bytes. |
| [`shape`](functions/shape.md) | Sheets | `shape(sheet)` | Return a Sheet's row and column counts. |
| [`sheet`](functions/sheet.md) | Sheets | `sheet(columns)` | Construct an immutable Sheet from ordered columns. |
| [`sleep`](functions/sleep.md) | Simulation | `sleep(milliseconds)` | Block the Python reference host for a number of milliseconds. |
| [`some`](functions/some.md) | option | `some(..args)` | Wrap a present value in the Option success form `some(value)`. |
| [`some?`](functions/some-p.md) | option | `some?(value)` | Check whether a value is `some(...)`. |
| [`spawn`](functions/spawn.md) | process | `spawn(handler)` | Create a process handle backed by a host-thread mailbox worker. |
| [`split`](functions/split.md) | string | `split(value, sep)` | Split `value` on the explicit separator `sep`. |
| [`split_whitespace`](functions/split_whitespace.md) | string | `split_whitespace(value)` | Split a string on runs of whitespace. |
| [`starts_with`](functions/starts_with.md) | string | `starts_with(value, prefix)` | Check whether a string starts with a prefix. |
| [`stdin`](functions/stdin.md) | I/O | `stdin()` | Return the Python-host standard-input source capability. |
| [`step_ctx`](functions/step_ctx.md) | flow | `step_ctx(ctx)` | Replace the running `ctx` for later `refine(..steps)` steps and later input items. |
| [`step_emit`](functions/step_emit.md) | flow | `step_emit(x)` | Emit one output value from a `refine(..steps)` step. |
| [`step_emit_many`](functions/step_emit_many.md) | flow | `step_emit_many(xs)` | Emit a list of output values from a `refine(..steps)` step. |
| [`step_halt`](functions/step_halt.md) | flow | `step_halt()` | Stop later `refine(..steps)` steps for the current input item. |
| [`step_set`](functions/step_set.md) | flow | `step_set(record)` | Replace the current record for later `refine(..steps)` steps on the same input item. |
| [`step_skip`](functions/step_skip.md) | flow | `step_skip()` | Return `none` for a `refine(..steps)` step with no effect. |
| [`step_step`](functions/step_step.md) | flow | `step_step(record, ctx, out)` | Replace `record`, replace `ctx`, and emit `out` in one `refine(..steps)` step. |
| [`stream_cons`](functions/stream_cons.md) | stream | `stream_cons(head, tail_fn)` | Construct a stream node from a head value and delayed tail function. |
| [`stream_filter`](functions/stream_filter.md) | stream | `stream_filter(pred, s)` | Lazily keep only stream elements where `pred(x)` is `true`. |
| [`stream_head`](functions/stream_head.md) | stream | `stream_head(s)` | Return the head value of a stream pair. |
| [`stream_map`](functions/stream_map.md) | stream | `stream_map(f, s)` | Lazily map a function over a stream. |
| [`stream_tail`](functions/stream_tail.md) | stream | `stream_tail(s)` | Force and return the tail of a stream pair. |
| [`stream_take`](functions/stream_take.md) | stream | `stream_take(n, s)` | Materialize the first `n` stream elements as an ordinary list. |
| [`strip_representation`](functions/strip_representation.md) | Value templates | `strip_representation(format, value)` | Remove one matching representation facet from a represented value. |
| [`sum`](functions/sum.md) | math | `sum(xs)` | Add all numeric elements of a list. |
| [`symbol_expr?`](functions/symbol_expr-p.md) | syntax | `symbol_expr?(expr)` | Check whether a quoted expression is a symbol/variable expression. |
| [`tagged_list?`](functions/tagged_list-p.md) | syntax | `tagged_list?(expr, tag)` | Check whether `expr` is a pair chain whose first item equals `tag`. |
| [`take`](functions/take.md) | list | `take(n, xs)` | Take the first `n` items from a list. |
| [`tap`](functions/tap.md) | fn | `tap(fn, value)` | Call `fn(value)` for side effects and return `value` unchanged. |
| [`tee`](functions/tee.md) | flow | `tee(flow)` | Split one input flow into two lazy branch flows. |
| [`text_of_quotation`](functions/text_of_quotation.md) | syntax | `text_of_quotation(expr)` | Return the contents of a quoted form. |
| [`then_find`](functions/then_find.md) | option | `then_find(needle, target)` | Find `needle` in a string target within a pipeline, returning its index as an Option. |
| [`then_first`](functions/then_first.md) | option | `then_first(target)` | Take the first element of a list target within a pipeline, as an Option. |
| [`then_get`](functions/then_get.md) | option | `then_get(key, target)` | Look up `key` in a map target within a pipeline, returning an Option. |
| [`then_nth`](functions/then_nth.md) | option | `then_nth(index, target)` | Take the element at `index` of a list target within a pipeline, as an Option. |
| [`trace`](functions/trace.md) | fn | `trace(label, value)` | Log `label` and `value` for pipeline debugging, then return `value` unchanged. |
| [`trim`](functions/trim.md) | string | `trim(value)` | Trim leading and trailing whitespace. |
| [`trim_end`](functions/trim_end.md) | string | `trim_end(value)` | Trim trailing whitespace. |
| [`trim_start`](functions/trim_start.md) | string | `trim_start(value)` | Trim leading whitespace. |
| [`unwrap_or`](functions/unwrap_or.md) | option | `unwrap_or(default, opt)` | Unwrap `some(...)`, returning `default` for `none(...)`. |
| [`update_entry_bytes`](functions/update_entry_bytes.md) | File / zip | `update_entry_bytes(entry, updater)` | Return a zip entry after applying a bytes updater. |
| [`upper`](functions/upper.md) | string | `upper(value)` | Convert a string to uppercase. |
| [`utf8_decode`](functions/utf8_decode.md) | Encoding | `utf8_decode(bytes)` | Decode a byte value as UTF-8 text. |
| [`utf8_encode`](functions/utf8_encode.md) | Encoding | `utf8_encode(text)` | Encode a string as UTF-8 bytes. |
| [`validate_each`](functions/validate_each.md) | validation | `validate_each(source, validator)` | Apply a validator to each item in a list or Flow and return Outcomes. |
| [`validate_field`](functions/validate_field.md) | validation | `validate_field(field, predicate, expected, record)` | Validate a record field with a predicate and return an Outcome. |
| [`validate_optional`](functions/validate_optional.md) | validation | `validate_optional(field, record)` | Validate an optional record field and return an Outcome. |
| [`validate_record`](functions/validate_record.md) | validation | `validate_record(record, validators)` | Compose field validators over one record and return a record-level Outcome. |
| [`validate_required`](functions/validate_required.md) | validation | `validate_required(field, record)` | Require a record field and return an Outcome. |
| [`where`](functions/where.md) | Sheets | `where(sheet, predicate)` | Return a Sheet containing rows accepted by a predicate. |
| [`write`](functions/write.md) | io | `write(sink, value)` | Write the display form of `value` to `sink` without a trailing newline. |
| [`write_file`](functions/write_file.md) | file | `write_file(path, text)` | Write UTF-8 text content to `path`. |
| [`writeln`](functions/writeln.md) | io | `writeln(sink, value)` | Write the display form of `value` to `sink` followed by a newline. |
| [`zip`](functions/zip.md) | flow | `zip(pair)` | Combine two flows into a flow of pairs. |
| [`zip_entries`](functions/zip_entries.md) | File / zip | `zip_entries(path)` | Read a zip archive into a list of entry values. |
| [`zip_read`](functions/zip_read.md) | file | `zip_read(path)` | Create a lazy Flow of zip entries from `path`. |
| [`zip_write`](functions/zip_write.md) | file | `zip_write(path)` | Write zip items to `path` from a Flow or list. |

## By category

### AI composition

- [`model`](functions/model.md) - Construct a model callable through an explicit provider boundary.

### CLI

- [`argv`](functions/argv.md) - Return the trailing command-line arguments as a list of strings.

### Configuration

- [`config_args`](functions/config_args.md) - Normalize explicit program arguments into an R10 values-source descriptor.
- [`config_get`](functions/config_get.md) - Read and validate one configuration value through a provider.
- [`config_get_or`](functions/config_get_or.md) - Read and validate one configuration value or use an explicit default.
- [`config_provider`](functions/config_provider.md) - Construct an ordinary configuration provider from an explicit source.
- [`config_standard`](functions/config_standard.md) - Construct the conventional ordered configuration provider snapshot.
- [`config_view`](functions/config_view.md) - Construct a qualified configuration lookup callable over an explicit provider.
- [`declassify`](functions/declassify.md) - Declassify a protected value with matching explicit authority.
- [`protected_match`](functions/protected_match.md) - Match a value while preserving the protected carrier boundary.
- [`secret_get`](functions/secret_get.md) - Read and validate one protected secret through a provider.
- [`secret_get_or`](functions/secret_get_or.md) - Read and validate one protected secret or use an explicit protected default.
- [`secret_view`](functions/secret_view.md) - Construct a qualified protected-secret lookup callable over an explicit provider.

### Documentation

- [`doc`](functions/doc.md) - Return the canonical documentation string for a bound name.
- [`help`](functions/help.md) - Show the public help overview or documentation for one bound name.
- [`meta`](functions/meta.md) - Return the metadata map for a bound name.

### Encoding

- [`utf8_decode`](functions/utf8_decode.md) - Decode a byte value as UTF-8 text.
- [`utf8_encode`](functions/utf8_encode.md) - Encode a string as UTF-8 bytes.

### Evaluation

- [`force`](functions/force.md) - Force a delayed promise and return its value.

### File / zip

- [`entry_bytes`](functions/entry_bytes.md) - Return the bytes stored in a zip entry.
- [`entry_json`](functions/entry_json.md) - Return whether a zip entry name has a JSON suffix.
- [`entry_name`](functions/entry_name.md) - Return a zip entry's filename.
- [`set_entry_bytes`](functions/set_entry_bytes.md) - Return a zip entry with replacement bytes.
- [`update_entry_bytes`](functions/update_entry_bytes.md) - Return a zip entry after applying a bytes updater.
- [`zip_entries`](functions/zip_entries.md) - Read a zip archive into a list of entry values.

### Function helpers

- [`apply_raw`](functions/apply_raw.md) - Call a function with a list of positional arguments without automatic absence propagation.

### I/O

- [`debug_repr`](functions/debug_repr.md) - Return the deterministic debug representation of a value.
- [`display`](functions/display.md) - Return the display representation of a value.
- [`input`](functions/input.md) - Read one line from standard input.
- [`log`](functions/log.md) - Write values to standard error with a trailing newline.
- [`print`](functions/print.md) - Write values to standard output with a trailing newline.
- [`stdin`](functions/stdin.md) - Return the Python-host standard-input source capability.

### Lifecycle

- [`lifecycle_child`](functions/lifecycle_child.md) - Run a child execution scope nested under an active parent scope handle.
- [`lifecycle_context`](functions/lifecycle_context.md) - Read inward-only lifecycle context exposed by an entered peer or an ancestor scope.
- [`lifecycle_repeat`](functions/lifecycle_repeat.md) - Run a fresh element execution scope for each consumed list or flow element, exposing reserved element/index context.
- [`lifecycle_scope`](functions/lifecycle_scope.md) - Run a fresh root execution scope through explicit peer definitions and one work callable.

### Pairs

- [`car`](functions/car.md) - Return the first value of a pair.
- [`cdr`](functions/cdr.md) - Return the second value of a pair.
- [`cons`](functions/cons.md) - Construct a pair from two values.
- [`null?`](functions/null-p.md) - Return whether a value is the empty pair-list terminator.
- [`pair?`](functions/pair-p.md) - Return whether a value is a pair.

### Retrieval

- [`chunk`](functions/chunk.md) - Construct exact ordered chunks from a validated document and chunker callback.
- [`embed`](functions/embed.md) - Construct an embedding callable through an explicit provider boundary.
- [`index`](functions/index.md) - Construct an opaque retrieval index through an explicit provider boundary.
- [`rerank`](functions/rerank.md) - Construct a provenance-preserving reranker through an explicit provider boundary.
- [`retrieve`](functions/retrieve.md) - Construct a retrieval callable through an explicit provider boundary.

### Sheets

- [`collect_sheet`](functions/collect_sheet.md) - Collect homogeneous map records into an immutable Sheet.
- [`columns`](functions/columns.md) - Return a Sheet's column names in deterministic order.
- [`derive`](functions/derive.md) - Return a Sheet with one derived column.
- [`render_csv`](functions/render_csv.md) - Render an immutable Sheet as deterministic CSV text.
- [`row_get`](functions/row_get.md) - Read one named value from a Sheet row representation.
- [`rows`](functions/rows.md) - Return a Sheet's rows as ordered name/value pairs.
- [`select`](functions/select.md) - Return a Sheet containing selected columns.
- [`shape`](functions/shape.md) - Return a Sheet's row and column counts.
- [`sheet`](functions/sheet.md) - Construct an immutable Sheet from ordered columns.
- [`where`](functions/where.md) - Return a Sheet containing rows accepted by a predicate.

### Simulation

- [`sleep`](functions/sleep.md) - Block the Python reference host for a number of milliseconds.

### Testing

- [`assert_eq`](functions/assert_eq.md) - Assert that two values are equal.
- [`assert_true`](functions/assert_true.md) - Assert that a value is true.

### Validation

- [`collect_validated`](functions/collect_validated.md) - Collect Outcome values into clean values and diagnostics.

### Value templates

- [`exact_shape_match`](functions/exact_shape_match.md) - Match a value against an exact shape template.
- [`Format`](functions/Format-host.md) - Construct a tagged representation template.
- [`format_tag`](functions/format_tag.md) - Return the tag of a representation template.
- [`format_template`](functions/format_template.md) - Return the inner template of a representation template.
- [`open_shape_match`](functions/open_shape_match.md) - Match a value against an open shape template.
- [`refinement_match`](functions/refinement_match.md) - Match a value against a refinement template.
- [`represent`](functions/represent.md) - Attach a first-class representation facet to a value.
- [`representation_match`](functions/representation_match.md) - Match a represented value against a representation template.
- [`strip_representation`](functions/strip_representation.md) - Remove one matching representation facet from a represented value.

### actor

- [`actor`](functions/actor.md) - Create an actor with initial state and a message handler.
- [`actor_alive?`](functions/actor_alive-p.md) - Check whether an actor's worker thread is alive.
- [`actor_call`](functions/actor_call.md) - Send a message and wait for a reply (synchronous request-reply).
- [`actor_error`](functions/actor_error.md) - Return the actor error option.
- [`actor_failed?`](functions/actor_failed-p.md) - Check whether an actor has failed.
- [`actor_restart`](functions/actor_restart.md) - Restart a failed or stopped actor with a new initial state.
- [`actor_send`](functions/actor_send.md) - Send a message to an actor for asynchronous processing.
- [`actor_state`](functions/actor_state.md) - Read the current actor state without sending a message.
- [`actor_status`](functions/actor_status.md) - Return the actor status string.
- [`actor_stop`](functions/actor_stop.md) - Gracefully stop an actor after draining its mailbox.

### awk

- [`awk_count`](functions/awk_count.md) - Count rows that satisfy an AWK-style predicate.
- [`awk_filter`](functions/awk_filter.md) - Filter rows with an AWK-style predicate.
- [`awk_map`](functions/awk_map.md) - Map rows with AWK-style line numbering.
- [`awkify`](functions/awkify.md) - Apply an AWK-style row function over a list of rows.
- [`fields`](functions/fields.md) - Split a row into whitespace-separated fields, keeping the original row first.

### cell

- [`cell`](functions/cell.md) - Create a ready cell with initial state and no cached error.
- [`cell_alive?`](functions/cell_alive-p.md) - Check whether the cell worker thread is alive.
- [`cell_error`](functions/cell_error.md) - Return `none` when the cell is ready, or `some(error)` when failed.
- [`cell_failed?`](functions/cell_failed-p.md) - Check whether a cell is currently failed.
- [`cell_get`](functions/cell_get.md) - Read the current cell state.
- [`cell_send`](functions/cell_send.md) - Queue an asynchronous state update function for a cell.
- [`cell_state`](functions/cell_state.md) - Alias for `cell_get`.
- [`cell_status`](functions/cell_status.md) - Return `"ready"` or `"failed"`.
- [`cell_stop`](functions/cell_stop.md) - Gracefully stop a cell after draining its mailbox.
- [`cell_with_state`](functions/cell_with_state.md) - Create a ready cell backed by the provided ref.
- [`restart_cell`](functions/restart_cell.md) - Replace the cell state, clear cached failure, and mark the cell ready again.

### cli

- [`cli_flag?`](functions/cli_flag-p.md) - Check whether parsed options contain a truthy flag value.
- [`cli_option`](functions/cli_option.md) - Return a parsed option value when present.
- [`cli_option_or`](functions/cli_option_or.md) - Return a parsed option value or `default` when the option is missing.
- [`cli_parse`](functions/cli_parse.md) - Parse raw CLI args into `[opts, positionals]`, optionally using a minimal `flags` / `options` / `aliases` spec map.

### eval

- [`define`](functions/define.md) - Define a name in the current metacircular environment frame.
- [`empty_env`](functions/empty_env.md) - Create a fresh metacircular evaluation environment.
- [`eval`](functions/eval.md) - Evaluate a quoted Genia expression in a metacircular environment.
- [`extend`](functions/extend.md) - Create a child metacircular environment with lambda parameters bound to argument values.
- [`lookup`](functions/lookup.md) - Look up a symbol in a metacircular evaluation environment.
- [`set`](functions/set.md) - Rebind the nearest existing lexical name in a metacircular environment chain, or define it in the current frame when missing.

### file

- [`read_file`](functions/read_file.md) - Read a UTF-8 text file from `path`.
- [`write_file`](functions/write_file.md) - Write UTF-8 text content to `path`.
- [`zip_read`](functions/zip_read.md) - Create a lazy Flow of zip entries from `path`.
- [`zip_write`](functions/zip_write.md) - Write zip items to `path` from a Flow or list.

### flow

- [`as_seq`](functions/as_seq.md) - Explicitly adapt a list or string into a Seq-compatible ordered source.
- [`collect`](functions/collect.md) - Return list data from a list or by materializing a Flow.
- [`each`](functions/each.md) - Run `fn` for each item of a list or Flow, passing the original items through.
- [`evolve`](functions/evolve.md) - Create a Flow by repeatedly applying `step` to the previous value.
- [`keep_some`](functions/keep_some.md) - Keep only successful Option values from a flow.
- [`keep_some_else`](functions/keep_some_else.md) - Apply an Option-returning `stage` to each flow item, routing failures to `dead_handler`.
- [`lines`](functions/lines.md) - Create a Flow from `stdin`, an incoming Flow, or a list of strings.
- [`merge`](functions/merge.md) - Concatenate two flows into one output flow.
- [`refine`](functions/refine.md) - Apply step functions left-to-right to each incoming flow item.
- [`rule_ctx`](functions/rule_ctx.md) - Replace the running `ctx` for later `rules(..fns)` rules and later input items.
- [`rule_emit`](functions/rule_emit.md) - Emit one output value from a `rules(..fns)` rule.
- [`rule_emit_many`](functions/rule_emit_many.md) - Emit a list of output values from a `rules(..fns)` rule.
- [`rule_halt`](functions/rule_halt.md) - Stop later `rules(..fns)` rules for the current input item.
- [`rule_set`](functions/rule_set.md) - Replace the current record for later `rules(..fns)` rules on the same input item.
- [`rule_skip`](functions/rule_skip.md) - Return `none` for a `rules(..fns)` rule with no effect.
- [`rule_step`](functions/rule_step.md) - Replace `record`, replace `ctx`, and emit `out` in one `rules(..fns)` step.
- [`rules`](functions/rules.md) - Apply rule functions left-to-right to each incoming flow item.
- [`run`](functions/run.md) - Consume or traverse a list or Flow to completion and return nil.
- [`scan`](functions/scan.md) - Stateful flow transform driven by `step`.
- [`step_ctx`](functions/step_ctx.md) - Replace the running `ctx` for later `refine(..steps)` steps and later input items.
- [`step_emit`](functions/step_emit.md) - Emit one output value from a `refine(..steps)` step.
- [`step_emit_many`](functions/step_emit_many.md) - Emit a list of output values from a `refine(..steps)` step.
- [`step_halt`](functions/step_halt.md) - Stop later `refine(..steps)` steps for the current input item.
- [`step_set`](functions/step_set.md) - Replace the current record for later `refine(..steps)` steps on the same input item.
- [`step_skip`](functions/step_skip.md) - Return `none` for a `refine(..steps)` step with no effect.
- [`step_step`](functions/step_step.md) - Replace `record`, replace `ctx`, and emit `out` in one `refine(..steps)` step.
- [`tee`](functions/tee.md) - Split one input flow into two lazy branch flows.
- [`zip`](functions/zip.md) - Combine two flows into a flow of pairs.

### fn

- [`apply`](functions/apply.md) - Call `proc` with a list of positional arguments.
- [`compose`](functions/compose.md) - Compose functions right-to-left into one callable.
- [`inspect`](functions/inspect.md) - Log `value` for debugging and return it unchanged.
- [`tap`](functions/tap.md) - Call `fn(value)` for side effects and return `value` unchanged.
- [`trace`](functions/trace.md) - Log `label` and `value` for pipeline debugging, then return `value` unchanged.

### io

- [`clear_screen`](functions/clear_screen.md) - Clear the terminal screen and move the cursor to the top-left corner.
- [`flush`](functions/flush.md) - Flush an output sink.
- [`move_cursor`](functions/move_cursor.md) - Move the terminal cursor to column `x`, row `y`.
- [`render_grid`](functions/render_grid.md) - Render a simple text grid to stdout.
- [`write`](functions/write.md) - Write the display form of `value` to `sink` without a trailing newline.
- [`writeln`](functions/writeln.md) - Write the display form of `value` to `sink` followed by a newline.

### json

- [`json_decode`](functions/json_decode.md) - Decode JSON text or UTF-8 bytes through the portable JSON representation boundary.
- [`json_encode`](functions/json_encode.md) - Encode a supported ordinary or `json`-represented value as deterministic JSON.
- [`json_parse`](functions/json_parse.md) - Parse JSON text into Genia runtime data.
- [`json_pretty`](functions/json_pretty.md) - Compatibility alias for `json_stringify`.
- [`json_schema`](functions/json_schema.md) - Compile the supported JSON Schema structural subset into a Template.
- [`json_stringify`](functions/json_stringify.md) - Render a Genia value as deterministic pretty JSON.
- [`parse_csv_row`](functions/parse_csv_row.md) - Parse one CSV row into an Outcome.
- [`parse_jsonl_record`](functions/parse_jsonl_record.md) - Parse one JSONL object record into an Outcome.

### list

- [`any?`](functions/any-p.md) - Return `true` when any element satisfies a predicate.
- [`append`](functions/append.md) - Concatenate zero or more lists.
- [`count`](functions/count.md) - Count elements in a list.
- [`drop`](functions/drop.md) - Drop the first `n` items from a list.
- [`empty?`](functions/empty-p.md) - Check whether a list has no elements.
- [`filter`](functions/filter.md) - Keep elements where `predicate(x)` is `true`.
- [`find_opt`](functions/find_opt.md) - Canonical maybe-returning predicate-search helper for lists.
- [`first`](functions/first.md) - Return the first element as structured absence-aware Option.
- [`first_opt`](functions/first_opt.md) - Compatibility alias for `first(list)`.
- [`head`](functions/head.md) - Convenience alias for `take`.
- [`last`](functions/last.md) - Return the last element as an Option.
- [`length`](functions/length.md) - Count elements in a list.
- [`list`](functions/list.md) - Build a list from all provided arguments.
- [`map`](functions/map.md) - Apply a function to every list element.
- [`nil?`](functions/nil-p.md) - Check whether a value is `nil`.
- [`nth`](functions/nth.md) - Return the element at zero-based index `n` as structured absence-aware Option.
- [`nth_opt`](functions/nth_opt.md) - Compatibility alias for `nth(index, list)`.
- [`range`](functions/range.md) - Build a numeric range.
- [`reduce`](functions/reduce.md) - Fold a list from left to right.
- [`rest`](functions/rest.md) - Return all elements except the first.
- [`reverse`](functions/reverse.md) - Return a list with elements in reverse order.
- [`take`](functions/take.md) - Take the first `n` items from a list.

### map

- [`map_count`](functions/map_count.md) - Return the number of entries in a map.
- [`map_get`](functions/map_get.md) - Return the stored value for `key`, or `none("missing-key", {key: key})` when absent.
- [`map_has?`](functions/map_has-p.md) - Report whether a map contains `key`.
- [`map_item_key`](functions/map_item_key.md) - Return the key from a map item `[key, value]` pair.
- [`map_item_value`](functions/map_item_value.md) - Return the value from a map item `[key, value]` pair.
- [`map_items`](functions/map_items.md) - Return the entries of a map as a list of `[key, value]` pairs.
- [`map_keys`](functions/map_keys.md) - Return a list of all keys in a map.
- [`map_new`](functions/map_new.md) - Create an empty persistent map value.
- [`map_put`](functions/map_put.md) - Return a new map with `key` set to `value`.
- [`map_remove`](functions/map_remove.md) - Return a new map with `key` removed.
- [`map_values`](functions/map_values.md) - Return a list of all values in a map.
- [`pairs`](functions/pairs.md) - Zip two lists into a list of `[x, y]` pairs, bounded by the shorter input.

### math

- [`abs`](functions/abs.md) - Return the absolute value of a number.
- [`dec`](functions/dec.md) - Decrement a number by one.
- [`inc`](functions/inc.md) - Increment a number by one.
- [`max`](functions/max.md) - Return the larger of two numbers.
- [`min`](functions/min.md) - Return the smaller of two numbers.
- [`mod`](functions/mod.md) - Return the remainder of `a / b`.
- [`sum`](functions/sum.md) - Add all numeric elements of a list.

### option

- [`absence_context`](functions/absence_context.md) - Read the optional context metadata of a structured `none(...)` value.
- [`absence_meta`](functions/absence_meta.md) - Read the full metadata of a structured `none(...)` value as a map.
- [`absence_reason`](functions/absence_reason.md) - Read the reason label of a structured `none(...)` value.
- [`err`](functions/err.md) - Construct a recoverable Outcome failure value `err(reason)`.
- [`flat_map_some`](functions/flat_map_some.md) - Apply the Option-returning function `f` to the inner value of `some(value)`.
- [`get`](functions/get.md) - Look up `key` in a map target, returning an absence-aware Option.
- [`get?`](functions/get-p.md) - Compatibility alias for `get(key, target)`.
- [`is_none?`](functions/is_none-p.md) - Alias for `none?(opt)`.
- [`is_some?`](functions/is_some-p.md) - Alias for `some?(opt)`.
- [`map_some`](functions/map_some.md) - Apply `f` to the inner value of `some(value)`, returning `some(result)`.
- [`none?`](functions/none-p.md) - Check whether a value is any `none...` Option form.
- [`or_else`](functions/or_else.md) - Unwrap `some(...)`, falling back to `fallback` for `none(...)`.
- [`or_else_with`](functions/or_else_with.md) - Unwrap `some(...)`, calling `thunk()` for `none(...)`.
- [`some`](functions/some.md) - Wrap a present value in the Option success form `some(value)`.
- [`some?`](functions/some-p.md) - Check whether a value is `some(...)`.
- [`then_find`](functions/then_find.md) - Find `needle` in a string target within a pipeline, returning its index as an Option.
- [`then_first`](functions/then_first.md) - Take the first element of a list target within a pipeline, as an Option.
- [`then_get`](functions/then_get.md) - Look up `key` in a map target within a pipeline, returning an Option.
- [`then_nth`](functions/then_nth.md) - Take the element at `index` of a list target within a pipeline, as an Option.
- [`unwrap_or`](functions/unwrap_or.md) - Unwrap `some(...)`, returning `default` for `none(...)`.

### process

- [`process_alive?`](functions/process_alive-p.md) - Check whether a process worker is still alive.
- [`send`](functions/send.md) - Enqueue `message` for a process mailbox.
- [`spawn`](functions/spawn.md) - Create a process handle backed by a host-thread mailbox worker.

### random

- [`rand`](functions/rand.md) - Advance an explicit RNG state and return `[next_rng_state, float]`.
- [`rand_flow`](functions/rand_flow.md) - Return a lazy seeded Flow of floats in `[0, 1)`.
- [`rand_int`](functions/rand_int.md) - Advance an explicit RNG state and return `[next_rng_state, int]`.
- [`rand_int_flow`](functions/rand_int_flow.md) - Return a lazy seeded Flow of integers in `[0, n)`.
- [`rng`](functions/rng.md) - Create an explicit deterministic RNG state from `seed`.

### ref

- [`ref`](functions/ref.md) - Create a synchronized ref, optionally with an initial value.
- [`ref_get`](functions/ref_get.md) - Read the current value from a ref.
- [`ref_is_set`](functions/ref_is_set.md) - Check whether a ref currently holds a value.
- [`ref_set`](functions/ref_set.md) - Set a ref to `value` and return `value`.
- [`ref_update`](functions/ref_update.md) - Apply `updater` to the current ref value atomically and store the result.

### stream

- [`stream_cons`](functions/stream_cons.md) - Construct a stream node from a head value and delayed tail function.
- [`stream_filter`](functions/stream_filter.md) - Lazily keep only stream elements where `pred(x)` is `true`.
- [`stream_head`](functions/stream_head.md) - Return the head value of a stream pair.
- [`stream_map`](functions/stream_map.md) - Lazily map a function over a stream.
- [`stream_tail`](functions/stream_tail.md) - Force and return the tail of a stream pair.
- [`stream_take`](functions/stream_take.md) - Materialize the first `n` stream elements as an ordinary list.

### string

- [`byte_length`](functions/byte_length.md) - Return the UTF-8 byte length of a string.
- [`concat`](functions/concat.md) - Concatenate two strings.
- [`contains`](functions/contains.md) - Check whether `needle` occurs inside `haystack`.
- [`ends_with`](functions/ends_with.md) - Check whether a string ends with a suffix.
- [`find`](functions/find.md) - Find the first index of `needle` within `value`.
- [`format`](functions/format.md) - Render `template` by substituting placeholders from `values`.
- [`format_compose`](functions/format_compose.md) - Compose string templates and Format values into one reusable Format.
- [`is_empty`](functions/is_empty.md) - Check whether a string is empty.
- [`join`](functions/join.md) - Join the strings in `xs` with `sep` between elements.
- [`lower`](functions/lower.md) - Convert a string to lowercase.
- [`parse_int`](functions/parse_int.md) - Parse an integer from a string, with optional explicit base.
- [`split`](functions/split.md) - Split `value` on the explicit separator `sep`.
- [`split_whitespace`](functions/split_whitespace.md) - Split a string on runs of whitespace.
- [`starts_with`](functions/starts_with.md) - Check whether a string starts with a prefix.
- [`trim`](functions/trim.md) - Trim leading and trailing whitespace.
- [`trim_end`](functions/trim_end.md) - Trim trailing whitespace.
- [`trim_start`](functions/trim_start.md) - Trim leading whitespace.
- [`upper`](functions/upper.md) - Convert a string to uppercase.

### syntax

- [`application_expr?`](functions/application_expr-p.md) - Check whether `expr` is a quoted application form `(app operator operand1 operand2 ...)`.
- [`assignment_expr?`](functions/assignment_expr-p.md) - Check whether `expr` is an assignment form `(assign name value)`.
- [`assignment_name`](functions/assignment_name.md) - Return the assigned symbol from a quoted assignment expression.
- [`assignment_value`](functions/assignment_value.md) - Return the value expression from a quoted assignment expression.
- [`block_expr?`](functions/block_expr-p.md) - Check whether `expr` is a block form `(block ...)`.
- [`block_expressions`](functions/block_expressions.md) - Return the tail of a quoted block expression as a pair-chain sequence of subexpressions.
- [`branch_body`](functions/branch_body.md) - Return the quoted result/body expression of a match branch.
- [`branch_guard`](functions/branch_guard.md) - Return the quoted guard of a guarded match branch.
- [`branch_has_guard?`](functions/branch_has_guard-p.md) - Check whether a quoted match branch carries a guard expression.
- [`branch_pattern`](functions/branch_pattern.md) - Return the quoted pattern of a match branch.
- [`lambda_body`](functions/lambda_body.md) - Return the quoted lambda body.
- [`lambda_expr?`](functions/lambda_expr-p.md) - Check whether `expr` is a lambda form.
- [`lambda_params`](functions/lambda_params.md) - Return the quoted lambda parameter structure.
- [`match_branches`](functions/match_branches.md) - Return the quoted branch sequence of a match expression.
- [`match_expr?`](functions/match_expr-p.md) - Check whether `expr` is a quoted pattern-match form `(match ...)`.
- [`operands`](functions/operands.md) - Return the operand tail of a quoted application expression as a pair-chain sequence.
- [`operator`](functions/operator.md) - Return the operator/callee part of a quoted application expression.
- [`quasiquoted_expr?`](functions/quasiquoted_expr-p.md) - Check whether `expr` is a quasiquoted form `(quasiquote ...)`.
- [`quoted_expr?`](functions/quoted_expr-p.md) - Check whether `expr` is a quoted form `(quote ...)`.
- [`self_evaluating?`](functions/self_evaluating-p.md) - Check whether a quoted expression is self-evaluating.
- [`symbol_expr?`](functions/symbol_expr-p.md) - Check whether a quoted expression is a symbol/variable expression.
- [`tagged_list?`](functions/tagged_list-p.md) - Check whether `expr` is a pair chain whose first item equals `tag`.
- [`text_of_quotation`](functions/text_of_quotation.md) - Return the contents of a quoted form.

### validation

- [`diagnostic_error`](functions/diagnostic_error.md) - Create a field/index-aware error diagnostic map.
- [`diagnostic_field`](functions/diagnostic_field.md) - Return a diagnostic map's field.
- [`diagnostic_reason`](functions/diagnostic_reason.md) - Return a diagnostic map's reason.
- [`diagnostic_skipped`](functions/diagnostic_skipped.md) - Create a field/index-aware skipped diagnostic map.
- [`validate_each`](functions/validate_each.md) - Apply a validator to each item in a list or Flow and return Outcomes.
- [`validate_field`](functions/validate_field.md) - Validate a record field with a predicate and return an Outcome.
- [`validate_optional`](functions/validate_optional.md) - Validate an optional record field and return an Outcome.
- [`validate_record`](functions/validate_record.md) - Compose field validators over one record and return a record-level Outcome.
- [`validate_required`](functions/validate_required.md) - Require a record field and return an Outcome.
