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
