from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def http_capability_section() -> str:
    text = read_text("docs/host-interop/capabilities.md")
    start = text.index("### Group: HTTP Serving")
    end = text.index("### Group:", start + 1)
    return text[start:end]


def test_http_capability_pins_r7_public_surface_and_maturity() -> None:
    section = http_capability_section()

    assert "**Maturity:** Partial" in section
    assert "Python-host-only" in section
    assert "not part of the shared portable contract" in section
    assert "no shared web spec category" in section

    for helper in (
        "serve_http",
        "get",
        "post",
        "route_request",
        "response",
        "with_headers",
        "cors",
        "json",
        "text",
        "ok",
        "ok_text",
        "bad_request",
        "not_found",
    ):
        assert f"`{helper}`" in section


def test_http_capability_pins_routing_maps_and_service_model() -> None:
    section = http_capability_section()

    assert "query-stripped exact path" in section
    assert "source/list order" in section
    for request_key in (
        "method",
        "path",
        "query",
        "headers",
        "body",
        "raw_body",
        "client",
    ):
        assert f"`{request_key}`" in section

    assert "request header names are lowercase" in section
    assert "`status`, `headers`, and `body`" in section
    assert "synchronous and blocking" in section
    assert "`{host, port, handled_requests}`" in section


def test_http_capability_pins_header_cors_and_error_boundaries() -> None:
    section = http_capability_section()

    assert "`with_headers(headers, response)`" in section
    assert "single public response-header composition operation" in section
    assert "case-insensitive" in section
    assert "does not mutate" in section
    assert "`cors(policy, handler)`" in section
    assert "single public CORS operation" in section
    assert "`origin` and `access-control-request-method`" in section
    assert "bodyless `204`" in section
    assert "incomplete `OPTIONS`" in section
    assert "delegates" in section
    assert "`500 internal server error`" in section


def test_http_capability_explains_test_and_portability_boundary() -> None:
    section = http_capability_section()

    assert "Genia-native tests" in section
    assert "public value/wrapper behavior" in section
    assert "focused Python tests" in section
    assert "HTTP transport boundary" in section
    assert "no public `options(...)` route" in section
    assert "no extra `json`/`text` header arities" in section


def test_r7_release_page_records_runnable_browser_exchange() -> None:
    text = read_text("docs/releases/R7.md")

    assert "`examples/http_service.genia`" in text
    assert "web.route_request([" in text
    assert "web.json(" in text
    assert "web.cors(" in text
    assert "genia examples/http_service.genia --max-requests 2" in text
    assert "curl -i -X OPTIONS" in text
    assert "curl -i http://127.0.0.1:8080/info" in text
    assert "HTTP/1.0 204 No Content" in text
    assert "HTTP/1.0 200 OK" in text
    assert "access-control-allow-origin: http://localhost:5173" in text
    assert "content-type: application/json; charset=utf-8" in text
    assert '\"service\": \"genia\"' in text


def test_r8_binds_to_r7_without_a_second_cors_mechanism() -> None:
    roadmap = read_text("docs/strategy/release-roadmap.md")

    assert "`@cors` → the R7 `cors` wrapper" in roadmap
    assert "No second mechanism" in roadmap


def test_authoritative_and_host_inventories_include_landed_r7_helpers() -> None:
    state = read_text("GENIA_STATE.md")
    host_interop = read_text("docs/host-interop/HOST_INTEROP.md")

    inventory = (
        "`serve_http`, `get`, `post`, `route_request`, `response`, "
        "`with_headers`, `cors`, `json`, `text`, `ok`, `ok_text`, "
        "`bad_request`, and `not_found`"
    )
    assert inventory in state
    for helper in (
        "serve_http",
        "get",
        "post",
        "route_request",
        "response",
        "with_headers",
        "cors",
        "json",
        "text",
        "ok",
        "ok_text",
        "bad_request",
        "not_found",
    ):
        assert f"`{helper}`" in host_interop

    assert "not a shared semantic-spec category" in host_interop


def test_r9_completion_and_r10_contract_gate_stay_synchronized() -> None:
    roadmap = read_text("docs/strategy/release-roadmap.md")
    killer_workflow = read_text("docs/strategy/killer-workflow.md")
    llm_contract = read_text("docs/ai/LLM_CONTRACT.md")
    agents = read_text("AGENTS.md")
    releases = read_text("docs/releases/README.md")
    r7_page = read_text("docs/releases/R7.md")

    assert "Release R7 — Web Serving Ergonomics ✓ COMPLETE" in roadmap
    assert "Release R8 — Server Execution Mode" in roadmap
    assert "**Status: Complete.** Explicitly approved infrastructure work delivered after R7." in roadmap
    assert "Release R9 — Value Templates & Representations" in roadmap
    assert "**Status: Complete.** E9-1 through E9-7 delivered" in roadmap
    assert "**Status: Active; E10-1 through E10-4 implemented.**" in roadmap
    assert "Issue #586 approved" in roadmap
    assert "later R10 slices and R11-R12 require their own gates" in roadmap
    assert "R7 is complete" in killer_workflow
    assert "R9** completed the value-template and representation work" in killer_workflow
    assert "E10-4 protected-sink safety" in killer_workflow
    assert "R10 has an approved" in llm_contract
    assert "E10-4 protected-sink slices are implemented" in llm_contract
    assert "R9 — Value Templates & Representations is complete." in agents
    assert "R10 (Configuration & Secrets) has an approved contract" in agents
    assert "implemented E10-1" in agents
    assert "E10-4 protected-sink" in agents
    assert "[R7 — Web Serving Ergonomics](R7.md) ✓ COMPLETE" in releases
    assert "[R9 — Value Templates & Representations](R9.md) ✓ COMPLETE" in releases
    assert "Status: **Complete.**" in r7_page
