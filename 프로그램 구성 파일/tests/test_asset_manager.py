from hashlib import sha1

import pytest

from studyforge.asset_manager import save_image_asset


def test_save_image_asset_writes_file_and_returns_markdown_link(tmp_path):
    asset_root = tmp_path / "assets"
    content = b"image-bytes"

    saved = save_image_asset(
        asset_root,
        studyset_slug="예방약학-기말",
        content=content,
        content_type="image/png",
        alt_text="관련 표",
    )

    expected_name = f"img-{sha1(content).hexdigest()[:12]}.png"
    assert saved.relative_path == f"assets/예방약학-기말/{expected_name}"
    assert saved.markdown == f"![관련 표](assets/예방약학-기말/{expected_name})"
    assert (asset_root / "예방약학-기말" / expected_name).read_bytes() == content


def test_save_image_asset_preserves_studyset_folder_name_with_spaces(tmp_path):
    asset_root = tmp_path / "assets"
    content = b"image-bytes"

    saved = save_image_asset(
        asset_root,
        studyset_slug="의약화학 기말고사",
        content=content,
        content_type="image/png",
        alt_text="그림",
    )

    expected_name = f"img-{sha1(content).hexdigest()[:12]}.png"
    assert saved.relative_path == f"assets/의약화학 기말고사/{expected_name}"
    assert (asset_root / "의약화학 기말고사" / expected_name).exists()


def test_save_image_asset_rejects_non_image_content_type(tmp_path):
    with pytest.raises(ValueError, match="Unsupported image content type"):
        save_image_asset(
            tmp_path / "assets",
            studyset_slug="예방약학-기말",
            content=b"text",
            content_type="text/plain",
        )
