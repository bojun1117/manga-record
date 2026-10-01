import os
from collections.abc import Iterator

# 必須在 import app 之前設定：app.core.database 在 import 時就會讀設定。
# 強制覆蓋，避免讀到 .env 裡的開發/正式資料庫。
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
os.environ["DATABASE_URL"] = TEST_DATABASE_URL or "postgresql+psycopg://unused@localhost/unused"
os.environ["JWT_SECRET"] = "test-secret"
os.environ["ANTHROPIC_API_KEY"] = ""

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.engine import Engine, make_url  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.core.database import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.model import Base  # noqa: E402


@pytest.fixture(scope="session")
def engine() -> Iterator[Engine]:
    if not TEST_DATABASE_URL:
        # CI 上沒設定資料庫要直接失敗，不能讓資料庫測試默默被跳過
        if os.environ.get("CI"):
            pytest.fail("CI 必須設定 TEST_DATABASE_URL")
        pytest.skip("需要 TEST_DATABASE_URL（PostgreSQL）才能跑資料庫測試")
    # 測試會 drop/create 所有資料表，資料庫名稱必須含 test，避免誤刪開發或正式資料
    if "test" not in (make_url(TEST_DATABASE_URL).database or ""):
        pytest.exit("TEST_DATABASE_URL 的資料庫名稱必須包含 'test'", returncode=1)

    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def db(engine: Engine) -> Iterator[Session]:
    # 每個測試包在一個交易裡，結束後 rollback；service 裡的 commit 只會提交到 savepoint
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db: Session) -> Iterator[TestClient]:
    app.dependency_overrides[get_db] = lambda: db
    yield TestClient(app)
    app.dependency_overrides.clear()
