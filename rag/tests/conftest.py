import importlib
import os
import sys
from pathlib import Path
import shutil
import pytest

CFG_PATH = "rag.config"
APP_PATH = "rag.app"

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# rag/tests 目录
TESTS_DIR = PROJECT_ROOT / "rag" / "tests"
# TESTS_DIR = Path("/Users/jialuyu/2025 T2/9900/rag-0814/capstone-project-25t2-9900-h16c-bread1/rag/tests")

DB0  = TESTS_DIR / "test_kb_mode0.db"
IMG0 = TESTS_DIR / "test_imgs_mode0"
UP0  = TESTS_DIR / "test_uploads_mode0"


DB1  = TESTS_DIR / "test_milvus_mode1.db"
IMG1 = TESTS_DIR / "test_imgs_mode1"
UP1  = TESTS_DIR / "test_uploads_mode1"


def _reload_module(mod_path: str):
    if mod_path in sys.modules:
        return importlib.reload(sys.modules[mod_path])
    return importlib.import_module(mod_path)


def _apply_cfg(mode: int, monkeypatch):
    cfg = importlib.import_module(CFG_PATH)
    if mode == 0:
        db, img = DB0, IMG0
    else:
        db, img = DB1, IMG1

    monkeypatch.setattr(cfg, "EMBEDDED_DB_PATH", str(db), raising=False)
    monkeypatch.setattr(cfg, "IMG_DIR",          str(img), raising=False)
    monkeypatch.setattr(cfg, "MODE",             mode,     raising=False)

    img.mkdir(parents=True, exist_ok=True)
    return cfg


def _ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)

@pytest.fixture(scope="session", autouse=True)
def _clean_mode_assets():
    for p in (DB0, DB1):
        try:
            p.unlink()
        except FileNotFoundError:
            pass
    for d in (IMG0, IMG1, UP0, UP1):
        if d.exists():
            shutil.rmtree(d, ignore_errors=True)

@pytest.fixture
def mk_app_client(monkeypatch):
    def _make(mode: int = 0):
        _apply_cfg(mode, monkeypatch)

        import rag.app as app_mod
        from rag.kb_manager import KnowledgeBaseManager

        up_dir = UP0 if mode == 0 else UP1
        _ensure_dir(up_dir)
        monkeypatch.setattr(app_mod, "TEMP_DIR", str(up_dir), raising=False)

        kb = KnowledgeBaseManager()        
        app_mod.app.config["KB_MANAGER"] = kb
        kb.mode = mode
        client = app_mod.app.test_client()
        assert getattr(kb, "mode", None) == mode
        return app_mod, client
    return _make


@pytest.fixture
def file_dir():
    p = Path(__file__).with_name("fixtures") 
    return str(p)
