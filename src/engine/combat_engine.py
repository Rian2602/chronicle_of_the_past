from src.engine.combat_interfaces import DamageResult
from src.engine import rule_engine
from src.systems import status_system


def magic_damage(power, attacker_int, defender_magic_res) -> int:
    return max(1, round(power + attacker_int * 0.5 - defender_magic_res))


def resolve_hit(state, attacker_stats, defender_stats, defender_id, power=0, is_magic=False, effects=None) -> DamageResult:
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
