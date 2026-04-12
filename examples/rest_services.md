# REST Service Examples

These examples are runnable against Genia's current host-backed HTTP surface:

- exact-path routing with `web/get(...)` and `web/post(...)`
- request maps with `method`, `path`, `query`, `headers`, `body`, `raw_body`, and `client`
- response maps built with `web/json(...)`, `web/ok_text(...)`, `web/bad_request(...)`, or `web/response(...)`
- in-memory state via `ref`, `ref_get`, `ref_set`, and `ref_update`
- blocking/synchronous serving through `web/serve_http(...)`

Request map notes:

- `headers` uses lowercased string keys
- `body` is parsed JSON when the request content type starts with `application/json`
- non-JSON request bodies stay as decoded text in both `body` and `raw_body`
- `client` is a map with `host` and `port`

Response map notes:

- `status`, `headers`, and `body` are the full phase-1 transport boundary
- response bodies at the transport boundary are string, bytes, or `none`
- invalid handler response shapes return `500 internal server error` in this phase

## Included examples

- `examples/rest_todo_service.genia`
  - `GET /todos`
  - `POST /todos/create`
  - `POST /todos/complete`
- `examples/rest_webhook_service.genia`
  - `POST /webhooks/events`
  - `GET /webhooks/events`
- `examples/rest_metrics_service.genia`
  - `POST /metrics/track`
  - `GET /metrics/summary`
- `examples/rest_feature_flags.genia`
  - `GET /flags?user=alice`
  - `POST /flags/set`
- `examples/rest_shortener_service.genia`
  - `POST /links`
  - `GET /links`
  - `GET /resolve?code=docs`

## Run one

```bash
python3 -m genia.interpreter examples/rest_todo_service.genia --port 8081
```

Each example also accepts `--max-requests N`, which is handy for tests and one-shot demos.
