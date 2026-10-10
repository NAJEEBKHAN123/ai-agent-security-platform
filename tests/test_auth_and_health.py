def test_root_health(client):
    """Verify root health check endpoint returns 200 OK."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "AI Agent Security Platform" in data["service"]


def test_api_v1_health(client):
    """Verify API v1 health endpoint confirms database connectivity."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["database"] == "connected"


def test_login_invalid_credentials(client):
    """Verify authentication fails cleanly on invalid credentials."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent@agentsec.com", "password": "WrongPassword!"},
    )
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


def test_login_seeded_analyst(client):
    """Verify seeded reviewer/analyst account can authenticate and receive JWT token."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "analyst@agentsec.com", "password": "AnalystPass123!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["role"] == "reviewer"


def test_protected_route_without_token(client):
    """Verify accessing /auth/me without token returns 401 Unauthorized."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_protected_route_with_valid_token(client):
    """Verify authenticated user profile is retrieved with valid bearer token."""
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "analyst@agentsec.com", "password": "AnalystPass123!"},
    )
    token = login_resp.json()["access_token"]

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    user_data = response.json()
    assert user_data["email"] == "analyst@agentsec.com"
    assert user_data["role"] == "reviewer"


def test_user_registration_and_duplicate_prevention(client):
    """Verify new user registration works and enforces uniqueness."""
    import uuid
    new_email = f"test_user_{uuid.uuid4().hex[:8]}@agentsec.com"
    payload = {
        "email": new_email,
        "full_name": "Test User",
        "password": "SecurePassword123!",
        "role": "user",
    }
    # Register new user
    reg_resp = client.post("/api/v1/auth/register", json=payload)
    assert reg_resp.status_code == 201
    assert reg_resp.json()["email"] == new_email

    # Duplicate registration must fail
    dup_resp = client.post("/api/v1/auth/register", json=payload)
    assert dup_resp.status_code == 400
    assert "already exists" in dup_resp.json()["detail"]
