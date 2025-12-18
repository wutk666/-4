from app.models import BannedIP
from app import db

def login(client):
    return client.post('/login', data={'username':'admin','password':'admin'}, follow_redirects=True)

def test_ban_unban_flow(client):
    login(client)
    # ban IP
    rv = client.post('/ban_ip', json={'ip':'127.0.0.2','permanent':True})
    assert rv.status_code == 200
    assert rv.get_json().get('status') == 'ok'

    # check get_banned_ips
    rv2 = client.get('/get_banned_ips')
    data = rv2.get_json()
    assert any(item['ip']=='127.0.0.2' for item in data)

    # unban
    rv3 = client.post('/unban_ip', json={'ip':'127.0.0.2'})
    assert rv3.status_code == 200
    rv4 = client.get('/get_banned_ips')
    data2 = rv4.get_json()
    assert not any(item['ip']=='127.0.0.2' for item in data2)