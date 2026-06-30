"""数据库会话依赖事务边界测试。"""

from __future__ import annotations

import pytest

from api.infrastructure.database import session as db_session


class _FakeSession:
    def __init__(self):
        self.committed = False
        self.rolled_back = False

    async def commit(self):
        self.committed = True

    async def rollback(self):
        self.rolled_back = True


class _FakeSessionContext:
    def __init__(self, session: _FakeSession):
        self.session = session

    async def __aenter__(self):
        return self.session

    async def __aexit__(self, exc_type, exc, tb):
        return False


@pytest.mark.asyncio
async def test_get_db_commits_after_success(monkeypatch):
    """FastAPI 依赖成功走完响应后必须提交事务。"""
    fake_session = _FakeSession()
    monkeypatch.setattr(
        db_session,
        "AsyncSessionFactory",
        lambda: _FakeSessionContext(fake_session),
    )

    dependency = db_session.get_db()
    yielded = await anext(dependency)
    assert yielded is fake_session

    with pytest.raises(StopAsyncIteration):
        await dependency.asend(None)

    assert fake_session.committed is True
    assert fake_session.rolled_back is False


@pytest.mark.asyncio
async def test_get_db_rolls_back_on_handler_error(monkeypatch):
    """路由处理异常时必须回滚而不是提交半成品写入。"""
    fake_session = _FakeSession()
    monkeypatch.setattr(
        db_session,
        "AsyncSessionFactory",
        lambda: _FakeSessionContext(fake_session),
    )

    dependency = db_session.get_db()
    yielded = await anext(dependency)
    assert yielded is fake_session

    with pytest.raises(RuntimeError, match="boom"):
        await dependency.athrow(RuntimeError("boom"))

    assert fake_session.committed is False
    assert fake_session.rolled_back is True
