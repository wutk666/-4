import pytest
from app import create_app, db

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    # 使用 app.test_client 与 app_context，复用现有 DB（会创建表）
    with app.test_client() as c:
        with app.app_context():
            db.create_all()
        yield c