from pathlib import Path


def test_skill_generation_returns_draft(client):
    expert_text = (Path(__file__).resolve().parent.parent / "examples" / "expert_sop.txt").read_text(encoding="utf-8")
    payload = {
        "skill_name": "Treasury Outflow Audit",
        "domain": "blockchain-audit",
        "expert_text": expert_text,
        "notes": "Initial draft for review.",
    }
    r = client.post("/v1/skills/generate", json=payload)
    assert r.status_code == 200, r.text
    body = r.json()
    draft = body["draft"]
    assert draft["id"]
    assert draft["name"] == "Treasury Outflow Audit"
    assert draft["system_instruction"]
    assert draft["output_schema"] in {"AuditReport", "SkillDefinition"}
    assert isinstance(draft["allowed_tools"], list) and len(draft["allowed_tools"]) >= 1
    assert body["yaml_preview"].startswith("id:")
