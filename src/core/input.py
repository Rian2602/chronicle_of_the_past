"""Parser perintah pemain (GDD §18): alias, argumen, dan error jelas."""

from __future__ import annotations

import difflib
from dataclasses import dataclass

# Alias Indonesia -> perintah kanonik (GDD §18.1–18.3).
ALIASES: dict[str, str] = {
    # Global (§18.1)
    "help": "help",
    "status": "status",
    "inventory": "inventory",
    "tas": "inventory",
    "quests": "quests",
    "misi": "quests",
    "memories": "memories",
    "memori": "memories",
    "map": "map",
    "party": "party",
    "tim": "party",
    "save": "save",
    "load": "load",
    "settings": "settings",
    "pengaturan": "settings",
    "quit": "quit",
    "keluar": "quit",
    # Eksplorasi (§18.2)
    "go": "go",
    "look": "look",
    "amat": "look",
    "talk": "talk",
    "bicara": "talk",
    # Pilihan dialog/event (§12.5, §15.3): UI klik mengirim
    # "choose <nomor>" (dialog) atau "choose <key>" (prompt_choice).
    "choose": "choose",
    "cultivate": "cultivate",
    "kultivasi": "cultivate",
    "breakthrough": "breakthrough",
    "terobosan": "breakthrough",
    "meditate": "rest",
    "meditasi": "rest",
    "rest": "rest",
    "istirahat": "rest",
    "refine": "refine",
    "racik": "refine",
    "formation": "formation",
    "formasi": "formation",
    "equip": "equip",
    "unequip": "unequip",
    "use": "use",
    "recall": "recall",
    "shop": "shop",
    "toko": "shop",
    "buy": "buy",
    "beli": "buy",
    "sell": "sell",
    "jual": "sell",
    # Combat (§18.3)
    "attack": "attack",
    "serang": "attack",
    "technique": "technique",
    "teknik": "technique",
    "defend": "defend",
    "bertahan": "defend",
    "item": "item",
    "pakai": "item",
    "observe": "observe",
    "amati": "observe",
    "swap": "swap",
    "ganti": "swap",
    "formation_skill": "formation_skill",
    "escape": "escape",
    "kabur": "escape",
}


class CommandError(ValueError):
    """Perintah tidak bisa diparsing: pesan jelas untuk pemain."""


# Nama kanonik dihitung sekali saat import (bukan tiap panggilan).
_KANONIK: list[str] = sorted({value for value in ALIASES.values()})


@dataclass(frozen=True)
class Command:
    """Perintah ter-parse: nama kanonik + argumen + input mentah."""

    name: str
    args: tuple[str, ...]
    raw: str


def _close_match(token: str, cutoff: float = 0.82) -> str | None:
    """Nama kanonik terdekat untuk token; None bila tak cukup dekat.

    Memakai difflib (stdlib) sebagai pengganti rapidfuzz — tangga
    Ponytail rung 3: pakai stdlib dulu.
    """
    matches = difflib.get_close_matches(token, _KANONIK, n=1, cutoff=cutoff)
    return matches[0] if matches else None


def complete_command(raw: str) -> str | None:
    """Autocomplete: nama kanonik untuk kata pertama input (TAB).

    Prefix yang tidak ambigu langsung dilengkapi; bila tidak ada prefix,
    typo ringan dikoreksi via difflib. Input kosong atau ambigu
    mengembalikan None.

    Args:
        raw: Input mentah pemain (bisa kosong atau berisi sebagian).

    Returns:
        Nama kanonik, atau None bila tidak ada yang dekat.
    """
    token = raw.strip().split()[0].lower() if raw.strip() else ""
    if not token:
        return None
    prefixes = [name for name in _KANONIK if name.startswith(token)]
    if len(prefixes) == 1:
        return prefixes[0]
    # ponytail: alias Indonesia (misi/tas/racik) belum bisa dilengkapi
    # TAB (prefix hanya cocokkan nama kanonik); upgrade bila perlu.
    return _close_match(token)


def parse_command(line: str) -> Command | None:
    """Parse satu baris input menjadi Command; None untuk baris kosong.

    Typo ringan pada kata pertama diperbaiki otomatis (difflib); typo
    jauh tetap CommandError.

    Raises:
        CommandError: perintah tidak dikenal (dan tidak ada koreksi dekat).
    """
    raw = line.strip()
    if not raw:
        return None
    parts = raw.split()
    alias = parts[0].lower()
    name = ALIASES.get(alias)
    if name is None:
        corrected = _close_match(alias)
        if corrected is not None:
            name = corrected
        else:
            raise CommandError(
                f"perintah tidak dikenal: '{alias}'. Ketik 'help'."
            )
    return Command(name=name, args=tuple(parts[1:]), raw=raw)
