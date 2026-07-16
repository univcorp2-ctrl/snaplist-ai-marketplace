from pathlib import Path

from fastapi.testclient import TestClient

import app.main as main


def make_client(tmp_path: Path) -> TestClient:
    main.settings.database_path = str(tmp_path / "test.db")
    main.init_db()
    return TestClient(main.app)


def test_health(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_analyze_returns_editable_draft(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    response = client.post(
        "/api/analyze",
        json={"file_name": "camera.jpg", "product_hint": "SEIKO 腕時計", "condition": "やや傷や汚れあり"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "SEIKO" in body["title"]
    assert body["price"]["low"] <= body["price"]["recommended"] <= body["price"]["premium"]
    assert len(body["samples"]) >= 3


def test_publish_own_store_and_assisted_marketplace(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    draft = client.post("/api/analyze", json={"product_hint": "カメラ"}).json()
    response = client.post(
        "/api/publish",
        json={"draft": draft, "platforms": ["own-store", "mercari"], "image_urls": []},
    )
    assert response.status_code == 200
    results = response.json()
    assert results[0]["mode"] == "published"
    assert results[1]["mode"] == "draft"
    listing = client.get(results[0]["url"])
    assert listing.status_code == 200


def test_static_pwa_files_exist() -> None:
    required = ["web/index.html", "web/app.js", "web/styles.css", "web/manifest.webmanifest", "web/sw.js"]
    for path in required:
        assert Path(path).is_file(), path
