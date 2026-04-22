import json
from pathlib import Path


def _load_example():
    p = Path(__file__).resolve().parent.parent / "examples" / "audit_request.json"
    return json.loads(p.read_text(encoding="utf-8"))


def test_mock_audit_run_returns_completed(client):
    payload = _load_example()
    r = client.post("/v1/audit/run", json=payload)
    assert r.status_code == 200, r.text
    body = r.json()

    assert body["status"] == "completed"
    assert body["skill_id"] == "asset_audit_basic"
    assert body["run_id"]
    assert body["markdown_report"]
    # Mock client invokes tools, so we expect at least one tool call.
    assert len(body["tool_calls"]) >= 1

    result = body["result"]
    assert result["report_id"]
    # Sample data is engineered to trigger anomalies.
    assert (len(result["findings"]) + len(result["anomalies"])) >= 1

    # Run history retrievable.
    runs = client.get("/v1/runs").json()
    assert any(r["run_id"] == body["run_id"] for r in runs)

    detail = client.get(f"/v1/runs/{body['run_id']}").json()
    assert detail["run_id"] == body["run_id"]
    assert detail["status"] == "completed"
    assert len(detail["tool_calls"]) >= 1
    assert detail["output_payload"]


def test_generic_agent_run_supports_additional_audit_skills(client):
    payload = _load_example()
    r = client.post(
        "/v1/agent/run",
        json={"skill_id": "counterparty_risk_review", "payload": payload},
    )
    assert r.status_code == 200, r.text
    body = r.json()

    assert body["status"] == "completed"
    assert body["skill_id"] == "counterparty_risk_review"
    assert body["run_id"]
    assert len(body["result"]["findings"]) + len(body["result"]["anomalies"]) >= 1
