import uuid
from fastapi.testclient import TestClient
from workbench import server, store


def test_artifact_download_stays_in_private_artifact_directory(tmp_path):
    client = TestClient(server.app)
    client.cookies.set("paw", store.TOKEN)
    ident = str(uuid.uuid4())
    outside = tmp_path / "outside.txt"
    outside.write_text("private fixture")
    store.put("artifacts", {"id": ident, "run": ident, "name": "outside.txt", "path": str(outside)})
    assert client.get("/api/artifacts/" + ident).status_code == 404
    assert client.get("/api/artifacts/" + ident + "/preview").status_code == 404
    root = store.STATE / "artifacts"
    root.mkdir(exist_ok=True)
    private = root / ident
    private.write_text("safe artifact")
    item = store.get("artifacts", ident)
    item["path"] = str(private)
    store.put("artifacts", item)
    response = client.get("/api/artifacts/" + ident)
    assert response.status_code == 200
    assert response.content == b"safe artifact"
    private.unlink()
    private.symlink_to(outside)
    assert client.get("/api/artifacts/" + ident).status_code == 404
