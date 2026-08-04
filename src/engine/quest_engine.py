from src.systems import level_system


def start_quest(game_state, quest_id) -> str:
    quest = game_state.quests.get(quest_id)
    if quest is None:
        return f"Quest tidak dikenal: {quest_id}."
    player = game_state.player
    if quest_id in player.quests_active:
        return "Quest sudah aktif."
    if quest_id in player.quests_done:
        return "Quest sudah selesai."
    player.quests_active[quest_id] = {"met": []}
    return f"Quest dimulai: {quest['title']}."


def complete_requirement(game_state, kind, target) -> str:
    player = game_state.player
    messages = []
    for quest_id in list(player.quests_active):
        quest = game_state.quests[quest_id]
        met = player.quests_active[quest_id]["met"]
        for index, requirement in enumerate(quest["requirements"]):
            if index in met:
                continue
            if requirement.get("kind") == kind and requirement.get("target") == target:
                met.append(index)
        if all(index in met for index in range(len(quest["requirements"]))):
            messages.append(_complete_quest(game_state, player, quest_id))
            next_quest = quest.get("next")
            if next_quest and next_quest != quest_id:
                messages.append(start_quest(game_state, next_quest))
    if not messages:
        return "Tidak ada syarat yang sesuai."
    return " ".join(messages)


def _complete_quest(game_state, player, quest_id) -> str:
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
