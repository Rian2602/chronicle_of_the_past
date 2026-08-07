import pytest
from src.core.input import Command
from src.core.game_loop import GameSession
import tempfile
from pathlib import Path

def _session():
    # Helper to create a new session with temp save dir
    tmp = Path(tempfile.mkdtemp())
    session = GameSession(save_dir=tmp)
    session.new_game("Dien")
    return session

def _dispatch(session: GameSession, raw: str):
    parts = raw.split()
    cmd = Command(name=parts[0], args=tuple(parts[1:]), raw=raw)
    return session.dispatch(cmd)

def test_sect_azure_map():
    session = _session()
    session.state.flags["map_sect_azure_unlocked"] = True
    
    _dispatch(session, "go sect_azure")
    assert session.state.location == "sect_azure"
    
    out = _dispatch(session, "look")
    log_text = "\n".join(out)
    assert "Sekte Awan Biru" in log_text

def test_fang_yue_intro():
    session = _session()
    session.state.location = "sect_azure"
    session.state.flags["quest108_done"] = True
    session.state.quests.started.append("quest201")
    
    _dispatch(session, "talk fang_yue")
    _dispatch(session, "choose 1")
    _dispatch(session, "choose 1")
    
    assert "quest201" in session.state.quests.done
    assert "quest202" in session.state.quests.started

def test_alchemist_xiu_quest():
    session = _session()
    session.state.location = "sect_azure"
    session.state.flags["quest201_done"] = True
    session.state.quests.started.append("quest202")
    
    _dispatch(session, "talk alchemist_xiu")
    
    assert "quest202" in session.state.quests.done
    assert "quest203" in session.state.quests.started
