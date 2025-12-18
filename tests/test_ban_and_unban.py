from app.models import BannedIP

def login(client):
    return client.post('/login', data={'username':'admin','password':'admin'}, follow_redirects=True)

def test_ban_and_unban_flow(client):
    login(client)
    ip = '127.0.0.2'

    # ban
    rv = client.post('/ban_ip', json={'ip': ip, 'permanent': True})
    assert rv.status_code == 200
    assert rv.get_json().get('status') == 'ok'

    # get list
    rv2 = client.get('/get_banned_ips')
    assert rv2.status_code == 200
    data = rv2.get_json()
    assert any(item['ip'] == ip for item in data)

    # unban
    rv3 = client.post('/unban_ip', json={'ip': ip})
    assert rv3.status_code == 200
    rv4 = client.get('/get_banned_ips')
    assert not any(item['ip'] == ip for item in rv4.get_json())