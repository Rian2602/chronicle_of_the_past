from src.systems import level_system


def start_quest(game_state, quest_id) -> str:
    """Aktifkan quest bila belum aktif/selesai.

    Setelah aktif, syarat flag/map yang sudah terpenuhi langsung
    ditandai; bila semua syarat langsung lengkap, quest langsung
    diselesaikan (rantai quest epilog memakai perilaku ini).

    Returns:
        Pesan konfirmasi dalam Bahasa Indonesia.
    """
    quest = game_state.quests.get(quest_id)
    if quest is None:
        return f"Quest tidak dikenal: {quest_id}."
    player = game_state.player
    if quest_id in player.quests_active:
        return "Quest sudah aktif."
    if quest_id in player.quests_done:
        return "Quest sudah selesai."
    player.quests_active[quest_id] = {"met": []}
    messages = [f"Quest dimulai: {quest['title']}."]
    # Tandai syarat flag/map yang sudah terpenuhi saat quest mulai.
    _prefill_satisfied(game_state, quest_id)
    info = player.quests_active[quest_id]
    requirements = quest["requirements"] or []
    if requirements and all(
        index in info["met"] for index in range(len(requirements))
    ):
        messages.append(_complete_quest(game_state, player, quest_id))
        next_quest = quest.get("next")
        if next_quest and next_quest != quest_id:
            messages.append(start_quest(game_state, next_quest))
    return " ".join(messages)


def _prefill_satisfied(game_state, quest_id):
    """Tandai syarat kind flag/map yang sudah terpenuhi pada quest aktif."""
    player = game_state.player
    info = player.quests_active.get(quest_id)
    if info is None:
        return
    quest = game_state.quests.get(quest_id)
    if quest is None:
        return
    current_map = getattr(game_state.current_map, "id", game_state.current_map)
    for index, requirement in enumerate(quest["requirements"]):
        if index in info["met"]:
            continue
        kind = requirement.get("kind")
        target = requirement.get("target")
        if kind == "flag" and target in game_state.flags:
            info["met"].append(index)
        elif kind == "map" and target == current_map:
            info["met"].append(index)


def complete_requirement(game_state, kind, target) -> str:
    """Tandai satu syarat quest sebagai terpenuhi dan selesaikan bila lengkap.

    Args:
        game_state: State permainan berisi quest aktif pemain.
        kind: Jenis syarat (talk/enemy/map/flag).
        target: Nilai target syarat (ID NPC/enemy/peta/flag).

    Returns:
        Pesan hasil, atau "Tidak ada syarat yang sesuai."
    """
    player = game_state.player
    if player is None:
        return "Tidak ada syarat yang sesuai."
    messages = []
    for quest_id in list(player.quests_active):
        quest = game_state.quests[quest_id]
        met = player.quests_active[quest_id]["met"]
        for index, requirement in enumerate(quest["requirements"]):
            if index in met:
                continue
            if (
                requirement.get("kind") == kind
                and requirement.get("target") == target
            ):
                met.append(index)
        _finalize_if_complete(game_state, player, quest_id, quest, messages)
    if not messages:
        return "Tidak ada syarat yang sesuai."
    return " ".join(messages)


def progress_requirement(
    game_state, kind, target, amount=1, to_map=None, from_map=None
) -> str:
    """Tambah progres syarat quest kind collect/kill_count/escort.

    Sesuai §12.1 story-season1-spec.md:
    - `collect`: `amount` adalah jumlah TOTAL item `target` yang kini
      dimiliki pemain (bukan penambahan). Progres disimpan sebagai nilai
      tertinggi yang pernah tercapai, sehingga menjual/memakai item
      setelahnya tidak membatalkan syarat yang sudah terpenuhi.
    - `kill_count`: `amount` adalah PENAMBAHAN jumlah musuh `target` yang
      dikalahkan (default 1 per panggilan), diakumulasikan per quest.
    - `escort`: `target` boleh None (cocok dengan NPC mana pun); syarat
      terpenuhi bila `to_map`/`from_map` sama persis dengan field
      `to`/`from` requirement. `amount` diabaikan.

    Args:
        game_state: State permainan berisi quest aktif pemain.
        kind: "collect", "kill_count", atau "escort".
        target: ID item/musuh/NPC target syarat (boleh None untuk escort).
        amount: Lihat penjelasan per kind di atas.
        to_map: Untuk escort — ID peta tujuan yang baru dicapai pemain.
        from_map: Untuk escort — ID peta asal sebelum perjalanan ini.

    Returns:
        Pesan hasil (termasuk penyelesaian quest bila lengkap), atau
        "Tidak ada syarat yang sesuai."
    """
    player = game_state.player
    if player is None:
        return "Tidak ada syarat yang sesuai."
    messages = []
    for quest_id in list(player.quests_active):
        quest = game_state.quests[quest_id]
        info = player.quests_active[quest_id]
        met = info["met"]
        progress = info.setdefault("progress", {})
        changed = False
        for index, requirement in enumerate(quest["requirements"]):
            if index in met:
                continue
            if requirement.get("kind") != kind:
                continue
            if kind == "escort":
                if (
                    requirement.get("to") != to_map
                    or requirement.get("from") != from_map
                ):
                    continue
                req_target = requirement.get("target")
                if target is not None and req_target != target:
                    continue
                met.append(index)
                changed = True
                continue
            if requirement.get("target") != target:
                continue
            needed = requirement.get("amount", 1)
            current = progress.get(target, 0)
            current = (
                max(current, amount) if kind == "collect" else current + amount
            )
            progress[target] = current
            changed = True
            if current >= needed:
                met.append(index)
        if changed:
            _finalize_if_complete(game_state, player, quest_id, quest, messages)
    if not messages:
        return "Tidak ada syarat yang sesuai."
    return " ".join(messages)


def _finalize_if_complete(game_state, player, quest_id, quest, messages):
    """Selesaikan quest & rantai `next` bila semua syarat sudah met."""
    met = player.quests_active[quest_id]["met"]
    requirements = quest["requirements"]
    if requirements and all(index in met for index in range(len(requirements))):
        messages.append(_complete_quest(game_state, player, quest_id))
        next_quest = quest.get("next")
        if next_quest and next_quest != quest_id:
            messages.append(start_quest(game_state, next_quest))


def _complete_quest(game_state, player, quest_id) -> str:
    """Berikan hadiah quest, set flag, dan pindahkan ke quests_done.

    Returns:
        Pesan penyelesaian quest beserta rincian hadiah.
    """
    quest = game_state.quests[quest_id]
    rewards = quest.get("rewards", {})
    gained_xp = level_system.award_xp(player, rewards.get("xp", 0))
    player.xp += gained_xp
    gold = rewards.get("gold", 0)
    player.gold += gold
    reputation = rewards.get("reputation", {})
    for faction, value in reputation.items():
        player.reputation[faction] = player.reputation.get(faction, 0) + value
    flags = quest.get("flags_on_complete")
    if isinstance(flags, str):
        flags = [flags]
    for flag in flags or []:
        game_state.flags[flag] = True
    player.quests_done.append(quest_id)
    del player.quests_active[quest_id]
    detail = []
    if gained_xp:
        detail.append(f"{gained_xp} XP")
    if gold:
        detail.append(f"{gold} emas")
    for faction, value in reputation.items():
        detail.append(f"{value} reputasi {faction}")
    message = f"Quest selesai: {quest['title']}."
    if detail:
        message += f" Hadiah: {', '.join(detail)}."
    return message


def fail_quest(game_state, quest_id) -> str:
    """Gagalkan quest aktif; hadiah & reputasi tidak diberikan.

    Quest dipindahkan ke `player.quests_failed` dan rantai `next`
    tetap dilanjutkan agar alur utama tidak terblokir (sesuai §12.3.2
    story-season1-spec.md — quest Arc 3 yang gagal otomatis saat
    ultimatum habis, alur utama tetap bisa dijalankan).

    Args:
        game_state: State permainan berisi quest aktif pemain.
        quest_id: ID quest yang digagalkan.

    Returns:
        Pesan konfirmasi dalam Bahasa Indonesia.
    """
    player = game_state.player
    if player is None:
        return "Tidak ada pemain."
    if quest_id not in player.quests_active:
        return f"Quest tidak aktif: {quest_id}."
    quest = game_state.quests.get(quest_id, {})
    del player.quests_active[quest_id]
    if quest_id not in player.quests_failed:
        player.quests_failed.append(quest_id)
    messages = [f"Quest gagal: {quest.get('title', quest_id)}."]
    next_quest = quest.get("next")
    if next_quest and next_quest != quest_id:
        if (
            next_quest not in player.quests_active
            and next_quest not in player.quests_done
            and next_quest not in player.quests_failed
        ):
            messages.append(start_quest(game_state, next_quest))
    return " ".join(messages)


def next_objective(game_state):
    """Tujuan pertama yang belum terpenuhi pada quest aktif, atau None."""
    player = game_state.player
    for quest_id in player.quests_active:
        quest = game_state.quests.get(quest_id)
        if quest is None:
            continue
        met = set(player.quests_active[quest_id].get("met", []))
        objectives = quest.get("objectives") or []
        for index, _ in enumerate(quest["requirements"]):
            if index not in met:
                text = (
                    objectives[index]
                    if index < len(objectives)
                    else quest.get("description", quest_id)
                )
                return f"{quest['title']} — {text}"
    return None
