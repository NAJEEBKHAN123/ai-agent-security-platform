import pytest
from app.security.output_scanner import output_scanner
from app.security.policy_engine import policy_engine
from app.models.user import User, UserRole


def test_output_scanner_detects_synthetic_secrets():
    """Verify synthetic secrets (DEMO_SECRET_...) are detected and redacted."""
    raw_output = "The confidential internal key is DEMO_SECRET_48291 and backup is FAKE_KEY_ROOT99."
    scan = output_scanner.scan_and_sanitize(raw_output)

    assert scan.has_leakage is True
    assert len(scan.leaks_detected) == 2
    assert "DEMO_SECRET_48291" not in scan.redacted_text
    assert "[REDACTED_SECRET: Synthetic Key]" in scan.redacted_text


def test_output_scanner_detects_aws_and_private_keys():
    """Verify cloud credentials and private key blocks are detected and redacted."""
    raw_output = (
        "Found access key AKIAIOSFODNN7EXAMPLE in repository.\n"
        "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA0Y1...\n-----END RSA PRIVATE KEY-----"
    )
    scan = output_scanner.scan_and_sanitize(raw_output)

    assert scan.has_leakage is True
    assert "AKIAIOSFODNN7EXAMPLE" not in scan.redacted_text
    assert "[REDACTED_CREDENTIAL: AWS Access Key]" in scan.redacted_text
    assert "[REDACTED_KEY: Private Key Block]" in scan.redacted_text


def test_output_scanner_clean_text():
    """Verify benign, clean output text passes without modifications."""
    benign_text = "The uptime calculation returned 99.86% availability across all web nodes."
    scan = output_scanner.scan_and_sanitize(benign_text)

    assert scan.has_leakage is False
    assert scan.redacted_text == benign_text
    assert len(scan.leaks_detected) == 0


def test_policy_engine_user_blocked_from_record_lookup(client):
    """Verify standard User is blocked from sensitive directory lookup tool."""
    # Register/login standard user
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "user@agentsec.com", "password": "UserPass123!"},
    )
    token = login_resp.json()["access_token"]

    # Chat requesting record lookup
    response = client.post(
        "/api/v1/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": "Look up directory record SEC-101"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["blocked"] is True
    assert data["decision"] == "Blocked"
    assert "requires role 'reviewer'" in data["response"]
    assert data["tools_invoked"][0]["status"] == "blocked_by_policy"


def test_policy_engine_reviewer_permitted_for_record_lookup(client):
    """Verify authorized Reviewer can execute directory lookup tool."""
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "analyst@agentsec.com", "password": "AnalystPass123!"},
    )
    token = login_resp.json()["access_token"]

    response = client.post(
        "/api/v1/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": "Look up directory record SEC-101"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["blocked"] is False
    assert data["decision"] == "Allowed"
    assert "Alice Chen" in data["response"]
    assert data["tools_invoked"][0]["status"] == "success"


def test_policies_list_api(client):
    """Verify all tool policies can be retrieved via the policies endpoint."""
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "user@agentsec.com", "password": "UserPass123!"},
    )
    token = login_resp.json()["access_token"]

    response = client.get(
        "/api/v1/policies",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    policies = response.json()
    assert len(policies) >= 4
    tool_names = [p["tool_name"] for p in policies]
    assert "safe_calculator" in tool_names
    assert "record_lookup" in tool_names
    assert "system_shell" in tool_names


def test_policy_update_restricted_to_admin(client):
    """Verify only Admin can modify security policy rules (RBAC enforcement)."""
    # 1. Standard user attempt should be 403 Forbidden
    user_login = client.post(
        "/api/v1/auth/login",
        json={"email": "user@agentsec.com", "password": "UserPass123!"},
    )
    user_token = user_login.json()["access_token"]

    forbidden_resp = client.patch(
        "/api/v1/policies/1",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"is_enabled": False, "allowed_role": "admin", "requires_approval": True},
    )
    assert forbidden_resp.status_code == 403

    # 2. Administrator attempt should succeed (200 OK)
    admin_login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@agentsec.com", "password": "AdminPass123!"},
    )
    admin_token = admin_login.json()["access_token"]

    allowed_resp = client.patch(
        "/api/v1/policies/1",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"is_enabled": True, "allowed_role": "user", "requires_approval": False},
    )
    assert allowed_resp.status_code == 200
    assert allowed_resp.json()["is_enabled"] is True
