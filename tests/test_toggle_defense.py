from app.models import Setting

def login(client):
    return client.post('/login', data={'username':'admin','password':'admin'}, follow_redirects=True)

def test_toggle_defense_api(client):
    login(client)
    rv = client.post('/toggle_defense', json={'enabled': False})
    assert rv.status_code == 200
    j = rv.get_json()
    assert j['enabled'] is False
    with client.application.app_context():
        s = Setting.query.filter_by(key='xss_defense_enabled').first()
        assert s is not None and s.value == '0'