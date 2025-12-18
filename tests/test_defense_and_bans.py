import pytest
from app.models import Setting

def login(client):
    return client.post('/login', data={'username':'admin','password':'admin'}, follow_redirects=True)

def test_toggle_defense_and_persistence(client):
    login(client)
    rv = client.post('/toggle_defense', json={'enabled': False})
    assert rv.status_code == 200
    assert rv.get_json().get('enabled') is False

    # 验证数据库中设置已持久化
    with client.application.app_context():
        s = Setting.query.filter_by(key='xss_defense_enabled').first()
        assert s is not None and s.value == '0'

    # 恢复开启
    rv2 = client.post('/toggle_defense', json={'enabled': True})
    assert rv2.status_code == 200
    assert rv2.get_json().get('enabled') is True