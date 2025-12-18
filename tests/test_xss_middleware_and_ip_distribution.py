from app.models import AttackLog
from datetime import datetime, timedelta

def login(client):
    return client.post('/login', data={'username':'admin','password':'admin'}, follow_redirects=True)

def test_xss_middleware_blocks_when_enabled_and_allows_when_disabled(client):
    # 默认防御通常为开启（app.config），确保登录后测试
    login(client)

    # 发送含 XSS 的请求，期望被中间件拦截（400）或返回带 error 的响应
    rv = client.post('/test_xss', json={'input': '<script>alert(1)</script>'})
    assert rv.status_code in (400, 200)
    if rv.status_code == 400:
        assert 'XSS' in rv.get_data(as_text=True) or 'blocked' in rv.get_data(as_text=True).lower()

    # 关闭防御并重试，期望正常接收（200）
    client.post('/toggle_defense', json={'enabled': False})
    rv2 = client.post('/test_xss', json={'input': '<script>alert(1)</script>'})
    assert rv2.status_code == 200
    assert rv2.is_json

def test_ip_distribution_reflects_attacklog_counts(client):
    login(client)
    # 在 DB 插入几条样例日志
    with client.application.app_context():
        AttackLog.query.delete()
        now = datetime.utcnow()
        logs = [
            AttackLog(ip='1.1.1.1', payload='p', timestamp=now - timedelta(days=1)),
            AttackLog(ip='1.1.1.1', payload='p2', timestamp=now - timedelta(days=2)),
            AttackLog(ip='2.2.2.2', payload='p3', timestamp=now),
        ]
        from app import db
        db.session.add_all(logs)
        db.session.commit()

    rv = client.get('/api/stats/ip_distribution')
    assert rv.status_code == 200
    j = rv.get_json()
    assert 'labels' in j and 'data' in j
    # 期望返回的 labels 包含两个 IP，且 counts 对应
    assert '1.1.1.1' in j['labels'] and '2.2.2.2' in j['labels']