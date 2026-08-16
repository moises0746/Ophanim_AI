from fastapi.testclient import TestClient

from ophanim.api.assistant_chat import get_chat_identity
from ophanim.domain.identifiers import TenantId, WorkspaceId
from ophanim.domain.identity import IdentityPrincipal
from ophanim.main import app
from ophanim.ports.identity import IdentityAuthenticationPort

client = TestClient(app)


class FakeIdentity(IdentityAuthenticationPort):
    def __init__(self, principal: IdentityPrincipal):
        self._principal = principal

    def authenticate_token(self, raw_token: str) -> IdentityPrincipal | None:
        if raw_token != "TEST_TOKEN":
            return None
        return self._principal


principal = IdentityPrincipal(
    tenant_id=TenantId("00000000-0000-0000-0000-000000000001"),
    workspace_id=WorkspaceId("00000000-0000-0000-0000-000000000002"),
    scopes=frozenset({"*"}),
)
app.dependency_overrides[get_chat_identity] = lambda: FakeIdentity(principal)

# Use the test identity token
HEADERS = {"Authorization": "Bearer TEST_TOKEN"}


def test_knowledge_upload_and_list():
    # 1. Upload document
    data = {
        "title": "My Test Doc",
        "uri_ref": "file:///test.md",
        "content": "# Test Document\n\nThis is a test paragraph for semantic search.",
    }

    response = client.post("/api/v1/knowledge/documents/upload", json=data, headers=HEADERS)
    assert response.status_code == 201
    doc = response.json()
    assert doc["title"] == "My Test Doc"
    assert doc["uri_ref"] == "file:///test.md"
    doc_id = doc["id"]

    # 2. List documents
    response = client.get("/api/v1/knowledge/documents", headers=HEADERS)
    assert response.status_code == 200
    docs = response.json()
    assert any(d["id"] == doc_id for d in docs)

    # 3. Search document
    search_req = {"query": "semantic search", "top_k": 5}
    response = client.post("/api/v1/knowledge/search", json=search_req, headers=HEADERS)
    assert response.status_code == 200
    search_res = response.json()

    assert search_res["query"] == "semantic search"
    assert len(search_res["citations"]) > 0
    citation = search_res["citations"][0]
    assert citation["document_id"] == doc_id
    assert "semantic search" in citation["excerpt"].lower()

    # 4. Delete document
    response = client.delete(f"/api/v1/knowledge/documents/{doc_id}", headers=HEADERS)
    assert response.status_code == 204

    # 5. Verify deleted
    response = client.get("/api/v1/knowledge/documents", headers=HEADERS)
    docs = response.json()
    assert not any(d["id"] == doc_id for d in docs)


def test_knowledge_search_invalid_source_filter():
    search_req = {"query": "test", "source_filters": ["invalid_type"]}
    response = client.post("/api/v1/knowledge/search", json=search_req, headers=HEADERS)
    assert response.status_code == 400
    assert "Invalid DocumentSourceType" in response.json()["detail"]


def test_knowledge_delete_not_found():
    response = client.delete("/api/v1/knowledge/documents/invalid-id-format", headers=HEADERS)
    assert response.status_code == 400

    response = client.delete(
        "/api/v1/knowledge/documents/00000000-0000-0000-0000-000000000000", headers=HEADERS
    )
    assert response.status_code == 404
