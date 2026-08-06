"""Parser perintah pemain (GDD §18): alias, argumen, dan error jelas."""

from __future__ import annotations

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
    "examine": "examine",
    "periksa": "examine",
    "loot": "loot",
    "rampas": "loot",
    "cultivate": "cultivate",
    "kultivasi": "cultivate",
    "breakthrough": "breakthrough",
    "terobosan": "breakthrough",
    "meditate": "meditate",
    "meditasi": "meditate",
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


@dataclass(frozen=True)
class Command:
    """Perintah ter-parse: nama kanonik + argumen + input mentah."""

    name: str
    args: tuple[str, ...]
    raw: str


def parse_command(line: str) -> Command | None:
    """Parse satu baris input menjadi Command; None untuk baris kosong.

    Raises:
        CommandError: perintah tidak dikenal.
    """
    raw = line.strip()
    if not raw:
        return None
    parts = raw.split()
    alias = parts[0].lower()
    name = ALIASES.get(alias)
    if name is None:
        raise CommandError(f"perintah tidak dikenal: '{alias}'. Ketik 'help'.")
    return Command(name=name, args=tuple(parts[1:]), raw=raw)
