from src.engine import quest_engine
from src.models.player import max_hp, max_mp
from src.systems import shop_system
from src.ui.renderer import bar


def render(player, game_state, npc_catalog=None):
    """Render HUD: nama, HP/MP bar, emas, XP, lokasi, dan tujuan quest.

    Args:
        player: Pemain yang ditampilkan.
        game_state: State permainan (lokasi, flag, quest aktif).
        npc_catalog: Katalog NPC (dict id → data) untuk hint toko;
            opsional — tanpa ini hint toko tidak ditampilkan.
    """
    location = game_state.current_map.name if game_state.current_map else "—"
    hp_bar = bar(player.hp, max_hp(player))
    mp_bar = bar(player.mp, max_mp(player))
    lines = [
        f"{player.name} — {player.class_id.title()} (Lv {player.level})",
        f"HP {player.hp}/{max_hp(player)} {hp_bar}",
        f"MP {player.mp}/{max_mp(player)} {mp_bar}",
        f"Emas: {player.gold}   XP: {player.xp}",
        f"Lokasi: {location}   Waktu: {game_state.time}",
    ]
    objective = quest_engine.next_objective(game_state)
    if objective:
        lines.append(f"▶ {objective}")
    ultimatum_line = _ultimatum_line(game_state)
    if ultimatum_line:
        lines.append(ultimatum_line)
    shop_hint = _shop_hint(game_state, npc_catalog)
    if shop_hint:
        lines.append(shop_hint)
    return "\n".join(lines)


def _ultimatum_line(game_state):
    """Baris hitung mundur ultimatum gereja (§12.3.2 story-season1-spec)."""
    if game_state.flags.get("ultimatum_resolved"):
        return None
    # Status expired tampil bahkan tanpa flag start, agar player tidak pernah
    # kehilangan konteks begitu api mulai (defensif terhadap urutan flag).
    if game_state.flags.get("ultimatum_expired"):
        return "🔥 Api telah dimulai. Inkuisisi bergerak."
    if "ultimatum_5_days" not in game_state.flags:
        return None
    days = int(game_state.flags.get("ultimatum_days_passed", 0))
    remaining = max(0, 5 - days)
    return f"🔥 Api dalam {remaining} hari"


def _shop_hint(game_state, npc_catalog=None):
    """Hint toko saat berada di peta yang punya NPC pedagang (§12.2)."""
    if not npc_catalog:
        return None
    current_map = game_state.current_map
    if current_map is None:
        return None
    npcs = getattr(current_map, "npcs", None)
    if not npcs:
        return None
    merchants = [
        npc_catalog.get(npc_id, {}).get("name", npc_id)
        for npc_id in npcs
        if shop_system.has_shop(npc_catalog.get(npc_id))
    ]
    if not merchants:
        return None
    return f"🛒 Toko tersedia: {', '.join(merchants)} (bicara untuk berbelanja)"
