r"""Validasi integritas dokumen sumber kebenaran (AGENTS.md §13).

Dokumen kontrol (GDD.md, AGENTS.md, CLAUDE.md) wajib bebas dari karakter
backslash yang merusak rendering markdown dan keterbacaan ID (mis.
`quest101\_done` tak lagi bisa di-grep). Ini menjaga agar korupsi
escaping yang pernah terjadi tidak kembali.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ("GDD.md", "AGENTS.md", "CLAUDE.md")


def test_dokumen_tidak_mengandung_backslash():
    """Setiap dokumen sumber kebenaran bebas dari backslash."""
    for name in DOCS:
        text = (ROOT / name).read_text(encoding="utf-8")
        assert "\\" not in text, f"{name}: mengandung karakter backslash"


def test_id_terkunci_terbaca_di_gdd():
    """ID kanonik di GDD terbaca sebagai string utuh (bukan terpecah)."""
    text = (ROOT / "GDD.md").read_text(encoding="utf-8")
    assert "elder_mao" in text
    assert "quest101_done" in text


def _section_gdd(start: str, end: str) -> str:
    """Ambil satu seksi GDD di antara dua penanda heading."""
    text = (ROOT / "GDD.md").read_text(encoding="utf-8")
    begin = text.index(start)
    finish = text.index(end, begin)
    return text[begin:finish]


def test_gdd_skema_quest_memakai_objectives_objek():
    """GDD §12.3: objectives quest adalah array objek (bukan array string).

    Konsisten dengan data/quests/quest101.json dan engine quest — label
    pemain dihasilkan dari objective_label, bukan disimpan sebagai string.
    """
    section = _section_gdd("### 12.3", "## 13")
    assert '{"kind": "talk", "target": "elder_mao"}' in section
    assert '"objectives": [' in section
    assert '"requirements"' not in section


def test_gdd_memuat_seksi_124_quest_engine():
    """GDD punya §12.4 Quest Engine (dirujuk AGENTS.md §5: 12.2–12.4)."""
    text = (ROOT / "GDD.md").read_text(encoding="utf-8")
    assert "### 12.4" in text
