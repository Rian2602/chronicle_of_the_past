import pytest

from src.ui.ascii_loader import load
from src.utils.json_loader import ContentError


def test_load_returns_file_text(tmp_path):
    (tmp_path / "village.txt").write_text("#..\n...", encoding="utf-8")
    assert load("village", assets_dir=str(tmp_path)) == "#..\n..."


def test_load_missing_raises(tmp_path):
    with pytest.raises(ContentError):
        load("tidak_ada", assets_dir=str(tmp_path))
