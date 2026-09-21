from fastapi.testclient import TestClient


def test_index_returns_200(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
