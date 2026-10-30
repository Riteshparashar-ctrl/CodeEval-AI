import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from evaluator.dataset import load_tasks  # noqa: E402
from evaluator.storage import connect  # noqa: E402


@pytest.fixture(scope="session")
def tasks():
    return load_tasks()


@pytest.fixture()
def task_by_id(tasks):
    return {t["id"]: t for t in tasks}


@pytest.fixture()
def conn(tmp_path):
    c = connect(tmp_path / "test.db")
    yield c
    c.close()
