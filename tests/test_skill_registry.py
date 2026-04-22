def test_skills_list_contains_defaults(client):
    r = client.get("/v1/skills")
    assert r.status_code == 200
    skills = r.json()
    ids = {s["id"] for s in skills}
    assert "asset_audit_basic" in ids
    assert "skill_generator_basic" in ids
    assert "counterparty_risk_review" in ids
    assert "ledger_reconciliation_review" in ids
    assert "approval_risk_review" in ids


def test_skills_get_one(client):
    r = client.get("/v1/skills/asset_audit_basic")
    assert r.status_code == 200
    s = r.json()
    assert s["id"] == "asset_audit_basic"
    assert "run_rule_based_checks" in s["allowed_tools"]


def test_skills_get_unknown(client):
    r = client.get("/v1/skills/does_not_exist")
    assert r.status_code == 404
    assert r.json()["error"] == "unknown_skill"


def test_new_skill_exposes_expected_tools(client):
    r = client.get("/v1/skills/counterparty_risk_review")
    assert r.status_code == 200
    skill = r.json()
    assert skill["output_schema"] == "AuditReport"
    assert "lookup_address_label" in skill["allowed_tools"]
    assert "run_rule_based_checks" in skill["allowed_tools"]
