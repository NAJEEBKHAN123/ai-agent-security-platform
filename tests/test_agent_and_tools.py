import pytest
from app.agent.tools import safe_calculator, document_summarizer, record_lookup


def test_safe_calculator_valid_arithmetic():
    """Verify safe calculator handles standard arithmetic accurately."""
    res1 = safe_calculator("25 * 4")
    assert "100" in res1

    res2 = safe_calculator("(100 - 20) / 4 + 5")
    assert "25" in res2

    res3 = safe_calculator("2 ** 8")
    assert "256" in res3


def test_safe_calculator_blocks_unsafe_code():
    """Verify calculator strictly blocks function calls, attribute access, and arbitrary code."""
    res_import = safe_calculator("__import__('os').system('ls')")
    assert "error" in res_import.lower()

    res_func = safe_calculator("print('hacked')")
    assert "error" in res_func.lower()

    res_var = safe_calculator("open('/etc/passwd')")
    assert "error" in res_var.lower()


def test_document_summarizer():
    """Verify document summarizer retrieves known policies and handles missing documents."""
    summary = document_summarizer("remote_work_policy")
    assert "Remote Work" in summary
    assert "VPN" in summary

    missing = document_summarizer("nonexistent_policy")
    assert "not found" in missing


def test_record_lookup():
    """Verify synthetic directory lookup retrieves records by ID."""
    found = record_lookup("SEC-101")
    assert "Alice Chen" in found
    assert "SOC Operations" in found

    not_found = record_lookup("SEC-999")
    assert "No record matching" in not_found


def test_chat_unauthenticated(client):
    """Verify unauthenticated chat request is rejected with 401 Unauthorized."""
    response = client.post("/api/v1/chat", json={"message": "Calculate 5 * 5"})
    assert response.status_code == 401


def test_chat_calculator_intent(client):
    """Verify authenticated chat invoking calculator executes tool and returns structured response."""
    # Authenticate as user
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "user@agentsec.com", "password": "UserPass123!"},
    )
    token = login_resp.json()["access_token"]

    response = client.post(
        "/api/v1/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": "Calculate (365 * 24 - 12) / (365 * 24) * 100"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["tools_invoked"]) > 0
    assert data["tools_invoked"][0]["tool_name"] == "safe_calculator"
    assert "99.86" in str(data["tools_invoked"][0]["output"])
    assert data["user_email"] == "user@agentsec.com"


def test_chat_document_intent(client):
    """Verify chat requesting document summary invokes document_summarizer."""
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "user@agentsec.com", "password": "UserPass123!"},
    )
    token = login_resp.json()["access_token"]

    response = client.post(
        "/api/v1/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": "Please summarize the remote work policy."},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["tools_invoked"]) > 0
    assert data["tools_invoked"][0]["tool_name"] == "document_summarizer"
    assert "VPN" in data["response"]


def test_chat_record_lookup_intent(client):
    """Verify authorized chat requesting record lookup queries the directory."""
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "analyst@agentsec.com", "password": "AnalystPass123!"},
    )
    token = login_resp.json()["access_token"]

    response = client.post(
        "/api/v1/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": "Look up record SEC-102."},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["tools_invoked"]) > 0
    assert data["tools_invoked"][0]["tool_name"] == "record_lookup"
    assert "Bob Vance" in data["response"]


def test_list_tools_endpoint(client):
    """Verify tools endpoint returns the registered safe tools."""
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "user@agentsec.com", "password": "UserPass123!"},
    )
    token = login_resp.json()["access_token"]

    response = client.get(
        "/api/v1/chat/tools",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    tools = response.json()
    tool_names = [t["name"] for t in tools]
    assert "safe_calculator" in tool_names
    assert "document_summarizer" in tool_names
    assert "record_lookup" in tool_names
