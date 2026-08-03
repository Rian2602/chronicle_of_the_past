from src.engine.combat_interfaces import StatusEffect

DOT_KINDS = {"poison", "burn", "bleed"}
CONTROL_KINDS = {"blind", "silence", "fear", "sleep"}

_LABELS = {
    "poison": "racun",
    "burn": "luka bakar",
    "bleed": "pendarahan",
    "blind": "kebutaan",
    "silence": "kebisuan",
    "fear": "ketakutan",
    "sleep": "tidur",
}


def _label(kind: str) -> str:
    return _LABELS.get(kind, kind)


def _resolve_actor(state, actor_id: str):
    if actor_id == "player":
        return state.player
    return state.enemy


def _actor_hp(actor, actor_id: str) -> int:
    if actor_id == "player":
        return actor.hp
    return actor.stats.get("hp", 0)


def _set_actor_hp(actor, actor_id: str, value: int) -> None:
    if actor_id == "player":
        actor.hp = value
    else:
        actor.stats["hp"] = value


def apply_status(state, actor_id: str, kind: str, power: int, duration: int) -> None:
    effects = state.statuses.setdefault(actor_id, [])
    for effect in effects:
        if effect.kind == kind:
            if kind in DOT_KINDS:
                effect.duration = min(
                    effect.duration + duration, state.max_status_duration
                )
            elif kind in CONTROL_KINDS:
                effect.duration = min(duration, state.max_status_duration)
            else:
                effect.duration = min(
                    effect.duration + duration, state.max_status_duration
                )
            return
    effects.append(
        StatusEffect(
            kind=kind,
            duration=min(duration, state.max_status_duration),
            power=power,
        )
    )


def tick_statuses(state, actor_id: str) -> list:
    effects = state.statuses.get(actor_id, [])
    if not effects:
        return []
    actor = _resolve_actor(state, actor_id)
    name = actor.name
    hp = _actor_hp(actor, actor_id)
    messages = []
    remaining = []
    for effect in effects:
        if effect.kind in DOT_KINDS:
            damage = min(effect.power, max(hp, 0))
            hp = max(0, hp - damage)
            messages.append(f"{name} terkena {_label(effect.kind)}, -{damage} HP.")
        effect.duration -= 1
        if effect.duration <= 0:
            messages.append(f"{_label(effect.kind).capitalize()} {name} hilang.")
        else:
            remaining.append(effect)
    _set_actor_hp(actor, actor_id, hp)
    state.statuses[actor_id] = remaining
    return messages
