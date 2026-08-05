from src.core.constants import CONTROL_KINDS, DOT_KINDS, STATUS_LABELS
from src.models.combat_interfaces import StatusEffect


def _label(kind: str) -> str:
    """Label tampilan Indonesia untuk satu jenis status effect."""
    return STATUS_LABELS.get(kind, kind)


def _resolve_actor(state, actor_id: str):
    """Ambil objek aktor (pemain atau musuh) sesuai actor_id."""
    if actor_id == "player":
        return state.player
    return state.enemy


def _actor_hp(actor, actor_id: str) -> int:
    """Baca HP aktor dari atribut yang sesuai dengan actor_id."""
    if actor_id == "player":
        return actor.hp
    return actor.stats.get("hp", 0)


def _set_actor_hp(actor, actor_id: str, value: int) -> None:
    """Tulis HP aktor ke atribut yang sesuai dengan actor_id."""
    if actor_id == "player":
        actor.hp = value
    else:
        actor.stats["hp"] = value


def apply_status(
    state, actor_id: str, kind: str, power: int, duration: int
) -> None:
    """Terapkan status effect ke aktor; effect sama digabung durasinya.

    DOT (racun/luka bakar/pendarahan) dan non-control memperpanjang
    durasi, sedangkan control (blind/silence/fear/sleep) di-reset.
    """
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
    """Proses efek status satu giliran: terapkan DOT dan kurangi durasi.

    Args:
        state: CombatState berisi statuses dan aktor.
        actor_id: "player" atau ID musuh.

    Returns:
        List pesan log (damage DOT, efek hilang) dalam Bahasa Indonesia.
    """
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
            messages.append(
                f"{name} terkena {_label(effect.kind)}, -{damage} HP."
            )
        effect.duration -= 1
        if effect.duration <= 0:
            messages.append(
                f"{_label(effect.kind).capitalize()} {name} hilang."
            )
        else:
            remaining.append(effect)
    _set_actor_hp(actor, actor_id, hp)
    state.statuses[actor_id] = remaining
    return messages


def actor_controlled(state, actor_id: str) -> bool:
    """True bila aktor masih di bawah status kontrol aktif (stun/sleep/dll).

    Status kontrol membuat aktor kehilangan giliran di combat (§9.4).
    """
    return any(
        effect.kind in CONTROL_KINDS
        for effect in state.statuses.get(actor_id, [])
    )


def slow_penalty(state, actor_id: str) -> int:
    """Total pengurang agility dari status `slow` aktif (§9.4 frost_bolt)."""
    return sum(
        effect.power
        for effect in state.statuses.get(actor_id, [])
        if effect.kind == "slow"
    )
