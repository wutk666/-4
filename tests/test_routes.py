import pytest
from app import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c

def test_login_page(client):
    rv = client.get('/login')
    assert rv.status_code == 200
    text = rv.get_data(as_text=True)
    assert ('登录' in text) or ('Login' in text)

if __name__ == "__main__":
    import sys
    import os
    os.system("source .venv/bin/activate")
    os.execvp(".venv/bin/python", [".venv/bin/python", "-m", "pytest", "-q"] + sys.argv[1:])