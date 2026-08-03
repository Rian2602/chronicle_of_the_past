from src.engine.combat_interfaces import CombatAction, CombatResult, CombatState, DamageResult
from src.engine import rule_engine
from src.models.player import max_hp, max_mp
from src.systems import inventory_system, status_system


def magic_damage(power, attacker_int, defender_magic_res) -> int:
    """Calculate magic damage based on power, intelligence and magic resistance."""
    return max(1, round(power + attacker_int * 0.5 - defender_magic_res))


def resolve_hit(state, attacker_stats, defender_stats, defender_id, power=0, is_magic=False, effects=None) -> DamageResult:
    """Resolve a hit between attacker and defender.
    
    Args:
        state: CombatState object
        attacker_stats: Attacker's statistics dictionary
        defender_stats: Defender's statistics dictionary
        defender_id: ID of the defender ("player" or enemy ID)
        power: Base power of the attack (for magic)
        is_magic: Whether this is a magic attack
        effects: Status effects to apply on hit
        
    Returns:
        DamageResult with damage, critical, and missed information
    """
    if defender_id == "player":
        defender_name = state.player.name
        attacker_name = state.enemy.name
    else:
        defender_name = state.enemy.name
        attacker_name = "Kamu"

    if is_magic:
        defender_magic_res = defender_stats.get("intelligence", 0) * 0.6
        attacker_int = attacker_stats.get("intelligence", 0)
        damage = magic_damage(power, attacker_int, defender_magic_res)
        critical = False
        missed = False
        log_line = f"{attacker_name} melontarkan mantra ke {defender_name}, -{damage} HP."
    else:
        roll = rule_engine.damage_roll(attacker_stats, defender_stats, state.randomizer)
        damage = roll["damage"]
        critical = roll["critical"]
        missed = roll["missed"]
        defending = (
            (defender_id == "player" and state.player_defending)
            or (defender_id != "player" and state.enemy_defending)
        )
        if not missed and defending:
            damage = damage // 2
        if missed:
            log_line = "Seranganmu meleset!" if attacker_name == "Kamu" else f"Serangan {attacker_name} meleset!"
        elif critical:
            log_line = f"Kritikal! {defender_name} terkena -{damage} HP."
        else:
            log_line = f"{attacker_name} menyerang {defender_name}, -{damage} HP."

    if defender_id == "player":
        state.player.hp = max(0, state.player.hp - damage)
    else:
        state.enemy.stats["hp"] = max(0, state.enemy.stats["hp"] - damage)

    if effects:
        for effect in effects:
            status_system.apply_status(
                state,
                defender_id,
                effect["kind"],
                effect["power"],
                effect["duration"],
            )

    state.log.append(log_line)
    return DamageResult(damage=damage, critical=critical, missed=missed)


def start_combat(player, enemy, randomizer, skills=None, loot_resolver=None, max_status_duration=10, items=None) -> CombatState:
    player_initiative = rule_engine.derived_stats(player, randomizer)["initiative"]
    enemy_initiative = enemy.stats.get("agility", 0) + randomizer.roll(0, 5)
    order = sorted(
        [("player", player_initiative), (enemy.id, enemy_initiative)],
        key=lambda entry: entry[1],
        reverse=True,
    )
    state = CombatState(
        round_no=1,
        turn_order=[entry[0] for entry in order],
        current_index=0,
        over=False,
        result=None,
        log=[],
        observe_used=False,
        player_defending=False,
        enemy_defending=False,
        statuses={},
        player=player,
        enemy=enemy,
        randomizer=randomizer,
        skills=skills or {},
        loot_resolver=loot_resolver,
        max_status_duration=max_status_duration,
        items=items or {},
    )
    state.enemy.stats["max_hp"] = state.enemy.stats.get("hp", 1)
    return state


def player_stats(state) -> dict:
    effective = {
        stat: state.player.base_stats.get(stat, 0)
        + state.player.attribute_bonuses.get(stat, 0)
        for stat in ("attack", "defense", "hp", "mp", "agility", "intelligence")
    }
    effective.update(rule_engine.derived_stats(state.player, state.randomizer))
    return effective


def enemy_stats(state) -> dict:
    return state.enemy.stats


def next_turn(state):
    if state.over:
        return
    if state.current_index == 0:
        state.current_index = 1
    else:
        state.current_index = 0
        state.round_no += 1


def _on_victory(state):
    state.result = CombatResult.VICTORY
    state.over = True
    reward = state.enemy.reward
    state.xp = reward.get("xp", 0)
    gold_range = reward.get("gold")
    if isinstance(gold_range, (list, tuple)) and len(gold_range) >= 2:
        state.gold = state.randomizer.roll(gold_range[0], gold_range[1])
    else:
        state.gold = 0
    state.loot = state.loot_resolver(state.enemy, state.randomizer) if state.loot_resolver is not None else []
    state.player.xp += state.xp
    state.player.gold += state.gold
    for entry in state.loot:
        inventory_system.add_item(state.player, entry["id"], entry.get("qty", 1))
    state.log.append(f"Kamu mendapat {state.xp} XP dan {state.gold} emas.")


def use_item(state, item_id) -> str | None:
    inventory = state.player.inventory
    item = next((entry for entry in inventory if entry["id"] == item_id), None)
    if item is None:
        raise ValueError(f"Item tidak dimiliki: {item_id}")
    item_def = state.items.get(item_id)
    heal = item_def.heal if item_def is not None and item_def.heal else item.get("heal")
    name = item_def.name if item_def is not None else item.get("name", item_id)
    if heal is None:
        message = "Item ini tidak bisa dipakai di pertarungan."
        state.log.append(message)
        return message
    item["qty"] -= 1
    if item["qty"] <= 0:
        inventory.remove(item)
    state.player.hp = min(max_hp(state.player), state.player.hp + heal)
    message = f"Kamu memakai {name}, memulihkan {heal} HP."
    state.log.append(message)
    return message


def _on_defeat(state):
    state.result = CombatResult.DEFEAT
    state.over = True


def _apply_player_regen(state):
    stats = player_stats(state)
    state.player.hp = min(max_hp(state.player), state.player.hp + int(stats["hp_regen"]))
    state.player.mp = min(max_mp(state.player), state.player.mp + int(stats["mana_regen"]))


def _hp_bar(enemy) -> str:
    current = enemy.stats.get("hp", 0)
    maximum = enemy.stats.get("max_hp", current or 1)
    filled = round(10 * current / maximum) if maximum else 0
    return "#" * filled + "." * (10 - filled)


def _weakness(stats) -> str:
    if stats.get("defense", 0) < 5:
        return "Lemah terhadap serangan fisik."
    if stats.get("intelligence", 0) < 5:
        return "Rentan terhadap sihir."
    return "Tidak ada kelemahan yang jelas."


def _resistance(stats) -> str:
    if stats.get("defense", 0) >= 10:
        return "Kebal terhadap serangan fisik."
    if stats.get("intelligence", 0) >= 10:
        return "Resisten terhadap sihir."
    return "Tidak ada ketahanan khusus."


def _hint(behavior) -> str:
    return {
        "aggressive": "Ia menyerang tanpa henti.",
        "defensive": "Ia cenderung bertahan.",
        "mage": "Ia gemar melontarkan sihir.",
        "coward": "Ia mungkin kabur saat terluka.",
    }.get(behavior, "Tingkah lakunya sulit diprediksi.")


def _observe_info(enemy, intelligence) -> str:
    lines = [f"{enemy.name} — HP {_hp_bar(enemy)}"]
    if intelligence >= 8:
        lines.append(f"Kelemahan: {_weakness(enemy.stats)}")
    if intelligence >= 13:
        lines.append(f"Ketahanan: {_resistance(enemy.stats)}")
        lines.append(f"Lore: {enemy.lore or 'Tidak ada catatan.'}")
    if intelligence >= 16:
        lines.append(f"HP tepat: {enemy.stats.get('hp', 0)}/{enemy.stats.get('max_hp', 1)}.")
        lines.append(f"Petunjuk: {_hint(enemy.behavior)}")
    return "\n".join(lines)


def _observe(state) -> bool:
    if state.observe_used:
        state.log.append("Kamu sudah mengamati musuh ini.")
        return False
    state.observe_used = True
    intelligence = state.player.base_stats.get("intelligence", 0) + state.player.attribute_bonuses.get("intelligence", 0)
    state.observe_info = _observe_info(state.enemy, intelligence)
    return True


def _escape(state) -> bool:
    player_agility = state.player.base_stats.get("agility", 0) + state.player.attribute_bonuses.get("agility", 0)
    enemy_agility = state.enemy.stats.get("agility", 0)
    if state.randomizer.roll(0, 100) < 50 + player_agility - enemy_agility:
        state.result = CombatResult.ESCAPED
        state.over = True
        state.log.append("Kamu berhasil melarikan diri!")
        return False
    state.log.append("Gagal melarikan diri!")
    resolve_hit(state, state.enemy.stats, player_stats(state), "player")
    if state.player.hp <= 0:
        _on_defeat(state)
    return False


def player_action(state, action, choice=None) -> bool:
    if state.over:
        return False
    state.player_defending = False
    messages = status_system.tick_statuses(state, "player")
    if messages:
        state.log.extend(messages)
    if state.player.hp <= 0:
        _on_defeat(state)
        return False
    _apply_player_regen(state)
    try:
        parsed = CombatAction(action)
    except ValueError:
        state.log.append("Aksi tidak dikenal.")
        return False
    if parsed is CombatAction.ATTACK:
        resolve_hit(state, player_stats(state), state.enemy.stats, state.enemy.id)
        if state.enemy.stats["hp"] <= 0:
            _on_victory(state)
        return False
    if parsed is CombatAction.DEFEND:
        state.player_defending = True
        state.log.append("Kamu bertahan!")
        return False
    if parsed is CombatAction.OBSERVE:
        return _observe(state)
    if parsed is CombatAction.ESCAPE:
        return _escape(state)
    if parsed in (CombatAction.SKILL, CombatAction.MAGIC):
        if choice not in state.skills:
            state.log.append("Skill tidak dikenal.")
            return False
        skill = state.skills[choice]
        if state.player.mp < skill["cost"]:
            state.log.append("MP tidak cukup.")
            return False
        state.player.mp -= skill["cost"]
        translated_effects = [
            {
                "kind": effect["status"],
                "power": effect.get("power", 0),
                "duration": effect.get("duration", 1),
            }
            for effect in skill.get("effects", [])
        ]
        if not translated_effects:
            translated_effects = None
        if skill["type"] == "magic":
            resolve_hit(
                state,
                player_stats(state),
                state.enemy.stats,
                state.enemy.id,
                power=skill["power"],
                is_magic=True,
                effects=translated_effects,
            )
        else:
            resolve_hit(
                state,
                player_stats(state),
                state.enemy.stats,
                state.enemy.id,
                effects=translated_effects,
            )
        if state.enemy.stats["hp"] <= 0:
            _on_victory(state)
        return False
    if parsed is CombatAction.ITEM:
        use_item(state, choice)
        return False
    state.log.append("Aksi tidak dikenal.")
    return False


def _translate_enemy_effects(skill):
    effects = [
        {
            "kind": effect["status"],
            "power": effect.get("power", 0),
            "duration": effect.get("duration", 1),
        }
        for effect in skill.get("effects", [])
    ]
    return effects or None


def _affordable_skills(state):
    return [
        state.skills[skill_id]
        for skill_id in state.enemy.skills
        if skill_id in state.skills
        and state.skills[skill_id]["cost"] <= state.enemy.stats["mp"]
    ]


def _use_enemy_skill(state, skill):
    state.enemy.stats["mp"] -= skill["cost"]
    if "heal" in skill:
        heal = skill["heal"]
        state.enemy.stats["hp"] = min(
            state.enemy.stats["max_hp"], state.enemy.stats["hp"] + heal
        )
        state.log.append(f"{state.enemy.name} memulihkan {heal} HP.")
        return
    effects = _translate_enemy_effects(skill)
    if skill["type"] == "magic":
        resolve_hit(
            state,
            state.enemy.stats,
            player_stats(state),
            "player",
            power=skill["power"],
            is_magic=True,
            effects=effects,
        )
    else:
        resolve_hit(
            state,
            state.enemy.stats,
            player_stats(state),
            "player",
            effects=effects,
        )


def _hp_ratio(state):
    maximum = state.enemy.stats.get("max_hp", state.enemy.stats["hp"]) or 1
    return state.enemy.stats["hp"] / maximum


def _aggressive_turn(state):
    affordable = _affordable_skills(state)
    if affordable:
        _use_enemy_skill(state, affordable[0])
        return
    resolve_hit(state, state.enemy.stats, player_stats(state), "player")


def _defensive_turn(state):
    if _hp_ratio(state) < 0.30:
        heal_skill = next(
            (skill for skill in _affordable_skills(state) if "heal" in skill),
            None,
        )
        if heal_skill is not None:
            _use_enemy_skill(state, heal_skill)
            return
    if state.enemy_defending:
        state.enemy_defending = False
        resolve_hit(state, state.enemy.stats, player_stats(state), "player")
        return
    state.enemy_defending = True
    state.log.append(f"{state.enemy.name} bertahan!")


def _mage_turn(state):
    affordable = _affordable_skills(state)
    magic = next((skill for skill in affordable if skill["type"] == "magic"), None)
    if magic is not None:
        _use_enemy_skill(state, magic)
        return
    if affordable:
        _use_enemy_skill(state, affordable[0])
        return
    resolve_hit(state, state.enemy.stats, player_stats(state), "player")


def _coward_turn(state):
    if _hp_ratio(state) < 0.20:
        state.log.append(f"{state.enemy.name} mencoba kabur tapi gagal!")
        return
    if state.enemy_defending:
        state.enemy_defending = False
        resolve_hit(state, state.enemy.stats, player_stats(state), "player")
        return
    state.enemy_defending = True
    state.log.append(f"{state.enemy.name} bertahan!")


def enemy_turn(state):
    if state.over:
        return
    messages = status_system.tick_statuses(state, state.enemy.id)
    if messages:
        state.log.extend(messages)
    if state.enemy.stats["hp"] <= 0:
        _on_victory(state)
        return
    behavior = state.enemy.behavior
    if behavior == "defensive":
        _defensive_turn(state)
    elif behavior == "mage":
        _mage_turn(state)
    elif behavior == "coward":
        _coward_turn(state)
    else:
        _aggressive_turn(state)
    if state.player.hp <= 0:
        _on_defeat(state)
