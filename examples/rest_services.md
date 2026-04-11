# REST Service Examples

These examples are runnable against Genia's current host-backed HTTP surface:

- exact-path routing with `web/get(...)` and `web/post(...)`
- request maps with `method`, `path`, `query`, `headers`, `body`, and `raw_body`
- response maps built with `web/json(...)`, `web/ok_text(...)`, `web/bad_request(...)`, or `web/response(...)`
- in-memory state via `ref`, `ref_get`, `ref_set`, and `ref_update`

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
