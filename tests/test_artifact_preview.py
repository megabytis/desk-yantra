import uuid
from pathlib import Path
import pytest
from fastapi import HTTPException
from workbench import server
from workbench.store import put, STATE


def test_artifact_text_endpoint(tmp_path):
    ident = str(uuid.uuid4())
    artifact_file = STATE / "artifacts" / ident
    artifact_file.parent.mkdir(parents=True, exist_ok=True)
    sample_text = "def hello():\n    return 'world'\n"
    artifact_file.write_text(sample_text, encoding="utf-8")

    put("artifacts", {
        "id": ident,
        "run": "run-1",
        "name": "hello.py",
        "path": str(artifact_file),
    })

    res = server.artifact_text(ident)
    assert res["id"] == ident
    assert res["name"] == "hello.py"
    assert res["content"] == sample_text
    assert res["size"] == len(sample_text.encode("utf-8"))
    assert res["truncated"] is False


def test_artifact_text_404_on_missing():
    with pytest.raises(HTTPException) as exc_info:
        server.artifact_text("nonexistent-artifact-id")
    assert exc_info.value.status_code == 404


def test_artifact_preview_safe_formats(tmp_path):
    # PNG
    png_id = str(uuid.uuid4())
    png_file = STATE / "artifacts" / png_id
    png_file.parent.mkdir(parents=True, exist_ok=True)
    png_file.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR...")
    put("artifacts", {"id": png_id, "run": "run-1", "name": "screen.png", "path": str(png_file)})
    res = server.preview(png_id)
    assert res.media_type == "image/png"

    # JPEG
    jpeg_id = str(uuid.uuid4())
    jpeg_file = STATE / "artifacts" / jpeg_id
    jpeg_file.write_bytes(b"\xff\xd8\xff\xe0\x00\x10JFIF...")
    put("artifacts", {"id": jpeg_id, "run": "run-1", "name": "photo.jpg", "path": str(jpeg_file)})
    res = server.preview(jpeg_id)
    assert res.media_type == "image/jpeg"

    # SVG
    svg_id = str(uuid.uuid4())
    svg_file = STATE / "artifacts" / svg_id
    svg_file.write_bytes(b"<svg xmlns='http://www.w3.org/2000/svg'><circle/></svg>")
    put("artifacts", {"id": svg_id, "run": "run-1", "name": "diagram.svg", "path": str(svg_file)})
    res = server.preview(svg_id)
    assert res.media_type == "image/svg+xml"

    # Unsupported binary
    bin_id = str(uuid.uuid4())
    bin_file = STATE / "artifacts" / bin_id
    bin_file.write_bytes(b"\x7fELF\x02\x01\x01\x00...")
    put("artifacts", {"id": bin_id, "run": "run-1", "name": "binary.bin", "path": str(bin_file)})
    with pytest.raises(HTTPException) as exc_info:
        server.preview(bin_id)
    assert exc_info.value.status_code == 415

