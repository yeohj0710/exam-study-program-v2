from pathlib import Path

from PIL import Image

from studyforge.legacy_importer import import_legacy_bank


def write_png(path: Path, color: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (32, 16), color).save(path)


def test_import_legacy_bank_roles_and_copies(tmp_path):
    legacy = tmp_path / "legacy"
    qdir = legacy / "의약화학 중간고사" / "1"
    write_png(qdir / "1.png", "white")
    write_png(qdir / "2.png", "blue")
    write_png(qdir / "3.png", "red")

    sources, cards, warnings = import_legacy_bank(legacy, tmp_path / "assets")

    assert warnings == []
    assert len(sources) == 1
    assert len(cards) == 1
    assert [asset.role for asset in cards[0].assets] == ["front_image", "choice_image", "answer_image"]
    for asset in cards[0].assets:
        assert (tmp_path / "assets" / asset.path).exists()


def test_import_legacy_ids_survive_image_replacement(tmp_path):
    legacy = tmp_path / "legacy"
    qdir = legacy / "deck" / "1"
    write_png(qdir / "1.png", "white")
    write_png(qdir / "2.png", "blue")

    first_sources, first_cards, _ = import_legacy_bank(legacy, tmp_path / "assets")
    write_png(qdir / "2.png", "red")
    second_sources, second_cards, _ = import_legacy_bank(legacy, tmp_path / "assets")

    assert first_sources[0].id == second_sources[0].id
    assert first_cards[0].id == second_cards[0].id
    assert first_cards[0].assets[-1].sha1 != second_cards[0].assets[-1].sha1


def test_import_legacy_copy_hashes_do_not_depend_on_asset_root(tmp_path):
    legacy = tmp_path / "legacy"
    qdir = legacy / "deck" / "1"
    write_png(qdir / "1.png", "white")
    write_png(qdir / "2.png", "blue")

    _, first_cards, _ = import_legacy_bank(legacy, tmp_path / "assets-a", copy_assets=True)
    _, second_cards, _ = import_legacy_bank(legacy, tmp_path / "assets-b", copy_assets=True)

    assert [asset.path for asset in first_cards[0].assets] == [asset.path for asset in second_cards[0].assets]
    assert [asset.sha1 for asset in first_cards[0].assets] == [asset.sha1 for asset in second_cards[0].assets]
