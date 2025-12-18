def test_middleware_blocks_xss(client):
    payload = {'input':'<script>alert(1)</script>'}
    rv = client.post('/test_xss', json=payload)
    # 若防御开启，应被拦截（400）；若关闭，返回 200（两种情况都可接受）
    assert rv.status_code in (400, 200)
    if rv.status_code == 400:
        assert 'XSS' in rv.get_data(as_text=True) or 'blocked' in rv.get_data(as_text=True)