from src.core.game_state import GameState
from src.models.item import Item
from src.models.player import Player
from src.systems.equipment_system import equip
from src.systems.inventory_system import add_item
from src.systems.shop_system import buy, has_shop, list_buy, list_sell, sell

POTION = Item("potion", "Potion", "consumable", heal=50, price=30)
HERB = Item("herb", "Herb", "consumable", heal=20, price=10)
STEEL_SWORD = Item(
    "steel_sword", "Steel Sword", "weapon", slot="weapon", price=120
)


def make_player(gold=100, level=1):
    return Player(
        name="Rian",
        class_id="warrior",
        hp=100,
        mp=20,
        base_stats={
            "attack": 10,
            "defense": 5,
            "hp": 100,
            "mp": 20,
            "agility": 8,
            "intelligence": 7,
        },
        gold=gold,
        level=level,
    )


def make_game_state(gold=100, level=1):
    gs = GameState()
    gs.player = make_player(gold=gold, level=level)
    gs.items = {"potion": POTION, "herb": HERB, "steel_sword": STEEL_SWORD}
    return gs


def make_npc(faction=None):
    return {
        "id": "marcus",
        "name": "Marcus",
        "faction": faction,
        "shop": {
            "buy": [
                {"item": "potion", "price": 25},
                {"item": "steel_sword", "price": 120},
            ],
            "sell_multiplier": 0.5,
        },
    }


def test_has_shop_true_for_npc_with_buy_list():
    assert has_shop(make_npc()) is True


def test_has_shop_false_for_npc_without_shop():
    assert has_shop({"id": "old_man", "name": "Aria"}) is False


def test_buy_success_deducts_gold_and_adds_item():
    gs = make_game_state(gold=100)
    npc = make_npc()
    msg = buy(gs, npc, "potion", 1)
    assert msg == "Kamu membeli Potion x1 seharga 25 emas."
    assert gs.player.gold == 75
    assert gs.player.inventory == [{"id": "potion", "qty": 1}]


def test_buy_multiple_quantity():
    gs = make_game_state(gold=100)
    npc = make_npc()
    msg = buy(gs, npc, "potion", 2)
    assert msg == "Kamu membeli Potion x2 seharga 50 emas."
    assert gs.player.gold == 50
    assert gs.player.inventory == [{"id": "potion", "qty": 2}]


def test_buy_insufficient_gold_rejected():
    gs = make_game_state(gold=10)
    npc = make_npc()
    msg = buy(gs, npc, "potion", 1)
    assert msg == "Emas tidak cukup untuk membeli Potion (25 emas)."
    assert gs.player.gold == 10
    assert gs.player.inventory == []


def test_buy_item_not_in_shop_rejected():
    gs = make_game_state(gold=100)
    npc = make_npc()
    msg = buy(gs, npc, "herb", 1)
    assert msg == "Item itu tidak dijual di sini."
    assert gs.player.gold == 100


def test_buy_npc_without_shop_rejected():
    gs = make_game_state(gold=100)
    msg = buy(gs, {"name": "Aria"}, "potion", 1)
    assert msg == "Aria tidak berjualan."
    assert gs.player.gold == 100


def test_buy_over_capacity_rejected_no_gold_deducted():
    gs = make_game_state(gold=10_000, level=1)
    add_item(gs.player, "herb", 30)  # dekati kapasitas (30 + level*2 = 32)
    npc = make_npc()
    msg = buy(gs, npc, "potion", 5)
    assert msg == "Tas penuh, tidak bisa membawa item lagi."
    assert gs.player.gold == 10_000


def test_buy_applies_merchant_guild_discount_at_threshold():
    gs = make_game_state(gold=100)
    gs.player.reputation["merchant_guild"] = 15
    npc = make_npc(faction="merchant_guild")
    msg = buy(gs, npc, "potion", 1)
    # 25 * 0.85 = 21.25 -> round to 21
    assert msg == "Kamu membeli Potion x1 seharga 21 emas."
    assert gs.player.gold == 79


def test_buy_no_discount_below_reputation_threshold():
    gs = make_game_state(gold=100)
    gs.player.reputation["merchant_guild"] = 10
    npc = make_npc(faction="merchant_guild")
    msg = buy(gs, npc, "potion", 1)
    assert msg == "Kamu membeli Potion x1 seharga 25 emas."


def test_buy_no_discount_for_non_merchant_guild_npc():
    gs = make_game_state(gold=100)
    gs.player.reputation["merchant_guild"] = 50
    npc = make_npc(faction=None)
    msg = buy(gs, npc, "potion", 1)
    assert msg == "Kamu membeli Potion x1 seharga 25 emas."


def test_sell_success_adds_gold_and_removes_item():
    gs = make_game_state(gold=0)
    add_item(gs.player, "potion", 1)
    npc = make_npc()
    msg = sell(gs, npc, "potion", 1)
    # potion.price=30 * 0.5 = 15
    assert msg == "Kamu menjual Potion x1 seharga 15 emas."
    assert gs.player.gold == 15
    assert gs.player.inventory == []


def test_sell_insufficient_stock_rejected():
    gs = make_game_state(gold=0)
    add_item(gs.player, "potion", 1)
    npc = make_npc()
    msg = sell(gs, npc, "potion", 2)
    assert msg == "Kamu tidak memiliki item itu sejumlah itu."
    assert gs.player.gold == 0
    assert gs.player.inventory == [{"id": "potion", "qty": 1}]


def test_sell_item_not_owned_rejected():
    gs = make_game_state(gold=0)
    npc = make_npc()
    msg = sell(gs, npc, "herb", 1)
    assert msg == "Kamu tidak memiliki item itu sejumlah itu."


def test_sell_equipped_item_rejected():
    gs = make_game_state(gold=0)
    add_item(gs.player, "steel_sword", 1)
    equip(gs.player, STEEL_SWORD, gs.items)
    assert gs.player.equipped == {"weapon": "steel_sword"}
    msg = sell(gs, make_npc(), "steel_sword", 1)
    assert msg == "Item yang sedang dipasang tidak bisa dijual."
    assert gs.player.gold == 0
    assert gs.player.equipped == {"weapon": "steel_sword"}
    assert gs.player.inventory == [{"id": "steel_sword", "qty": 1}]


def test_sell_npc_without_shop_rejected():
    gs = make_game_state(gold=0)
    add_item(gs.player, "potion", 1)
    msg = sell(gs, {"name": "Aria"}, "potion", 1)
    assert msg == "Aria tidak berjualan."
    assert gs.player.inventory == [{"id": "potion", "qty": 1}]


def test_list_buy_returns_effective_prices():
    gs = make_game_state(gold=100)
    npc = make_npc()
    result = list_buy(gs, npc)
    assert ("potion", "Potion", 25) in result
    assert ("steel_sword", "Steel Sword", 120) in result


def test_list_buy_applies_discount():
    gs = make_game_state(gold=100)
    gs.player.reputation["merchant_guild"] = 20
    npc = make_npc(faction="merchant_guild")
    result = list_buy(gs, npc)
    assert ("potion", "Potion", 21) in result


def test_list_sell_reflects_inventory():
    gs = make_game_state(gold=0)
    add_item(gs.player, "herb", 3)
    npc = make_npc()
    result = list_sell(gs, npc)
    assert ("herb", "Herb", 5, 3) in result


def test_list_sell_excludes_equipped_items():
    gs = make_game_state(gold=0)
    add_item(gs.player, "herb", 1)
    add_item(gs.player, "steel_sword", 1)
    equip(gs.player, STEEL_SWORD, gs.items)
    npc = make_npc()
    result = list_sell(gs, npc)
    assert all(item_id != "steel_sword" for item_id, *_ in result)
    assert ("herb", "Herb", 5, 1) in result


def test_buy_zero_or_negative_quantity_rejected():
    gs = make_game_state(gold=100)
    npc = make_npc()
    msg = buy(gs, npc, "potion", 0)
    assert msg == "Jumlah pembelian harus lebih dari nol."
    assert gs.player.gold == 100


def test_buy_quest_item_sets_quest_flag_and_met():
    """Beli item quest_flag setel flag & tandai syarat quest (§22.1 G-03)."""
    scroll = Item(
        "old_scroll",
        "Gulungan Kuno",
        "quest",
        price=30,
        quest_flag="have_old_scrolls",
    )
    gs = make_game_state(gold=100)
    gs.items["old_scroll"] = scroll
    gs.quests["quest017"] = {
        "id": "quest017",
        "title": "Sketsa dari Akademi",
        "requirements": [{"kind": "flag", "target": "have_old_scrolls"}],
        "rewards": {"xp": 0, "gold": 0, "reputation": {}},
    }
    gs.player.quests_active["quest017"] = {"met": []}
    npc = make_npc()
    npc["shop"]["buy"].append({"item": "old_scroll", "price": 30})
    buy(gs, npc, "old_scroll", 1)
    assert "have_old_scrolls" in gs.flags
    assert "quest017" in gs.player.quests_done
