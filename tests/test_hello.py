import pytest
from app import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c

def test_root_redirects(client):
    rv = client.get('/', follow_redirects=False)
    assert rv.status_code in (200, 302)

def test_login_page(client):
    rv = client.get('/login')
    assert rv.status_code == 200
    text = rv.get_data(as_text=True)
    assert ('登录' in text) or ('Login' in text)

def test_console_page(client):
    rv = client.get('/console')
    assert rv.status_code == 200
    text = rv.get_data(as_text=True)
    assert '防御与封禁管理' in text

    # Test ban IP functionality
    rv = client.post('/ban_ip', json={'ip': '127.0.0.1', 'permanent': True})
    assert rv.status_code == 200
    assert rv.get_json()['status'] == 'success'

    rv = client.post('/unban_ip', json={'ip': '127.0.0.1'})
    assert rv.status_code == 200
    assert rv.get_json()['status'] == 'success'

    # Test toggle defense functionality
    rv = client.post('/toggle_defense', json={'enabled': True})
    assert rv.status_code == 200
    assert rv.get_json()['status'] == 'defense enabled'

    rv = client.post('/toggle_defense', json={'enabled': False})
    assert rv.status_code == 200
    assert rv.get_json()['status'] == 'defense disabled'


async function banIp(ip, {permanent=false, duration=null} = {}){
  const body = { ip, permanent };
  if(duration) body.duration = duration;
  const r = await fetch('/ban_ip', {
    method: 'POST',
    credentials: 'same-origin',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify(body)
  });
  return r.json();
}

async function unbanIp(ip){
  const r = await fetch('/unban_ip', {
    method: 'POST',
    credentials: 'same-origin',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({ip})
  });
  return r.json();
}

async function toggleDefense(enabled){
  const r = await fetch('/toggle_defense', {
    method: 'POST',
    credentials: 'same-origin',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({enabled})
  });
  return r.json();
}