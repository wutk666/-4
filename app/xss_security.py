import re
import logging
from io import BytesIO
from collections import defaultdict
from flask import jsonify
from .models import AttackLog, BannedIP, Setting
from . import db
from datetime import datetime

class XSSDetector:
    xss_patterns = [
        r'<script[^>]*>.*?</script>',
        r'javascript\s*:',
        r'on\w+\s*=',
        r'alert\s*\(',
        r'eval\s*\(',
    ]

    @classmethod
    def detect_xss_patterns(cls, content: str) -> bool:
        if not content:
            return False
        for p in cls.xss_patterns:
            if re.search(p, content, re.IGNORECASE | re.DOTALL):
                return True
        return False

    @staticmethod
    def sanitize_content(content: str) -> str:
        return content.replace('<script>', '').replace('</script>', '').replace('javascript:', '')

class XSSMiddleware:
    def __init__(self, flask_app, app_wsgi):
        self.flask_app = flask_app
        self.app_wsgi = app_wsgi
        self.detector = XSSDetector()
        self.ip_attack_count = defaultdict(int)

    def _log_attack(self, ip, payload, blocked=True):
        with self.flask_app.app_context():
            log = AttackLog(ip=ip, payload=payload[:2000], blocked=blocked)
            db.session.add(log)
            db.session.commit()

    def is_defense_enabled(self):
        # 优先读取持久化设置，回退到 app.config
        try:
            with self.flask_app.app_context():
                s = Setting.query.filter_by(key='xss_defense_enabled').first()
                if s is not None:
                    return s.value == '1'
        except Exception:
            pass
        return bool(self.flask_app.config.get('XSS_DEFENSE_ENABLED', True))

    def check_ip_banned(self, ip):
        try:
            with self.flask_app.app_context():
                b = BannedIP.query.filter_by(ip=ip).first()
                if not b:
                    return False
                if b.permanent:
                    return True
                if b.expires_at and b.expires_at > datetime.utcnow():
                    return True
                # 过期则自动移除
                if b.expires_at and b.expires_at <= datetime.utcnow():
                    db.session.delete(b); db.session.commit()
                    return False
                return False
        except Exception:
            return False

    def __call__(self, environ, start_response):
        ip = environ.get('HTTP_X_FORWARDED_FOR', environ.get('REMOTE_ADDR', '127.0.0.1')).split(',')[0].strip()
        # 检查封禁
        if self.check_ip_banned(ip):
            body = b'{"error":"IP blocked"}'
            start_response('403 Forbidden', [('Content-Type','application/json; charset=utf-8'), ('Content-Length', str(len(body)))])
            return [body]

        # 仅在防御开启时拦截/检测
        if not self.is_defense_enabled():
            return self.app_wsgi(environ, start_response)

        # 只检查 JSON POST 体作为示例
        if environ.get('REQUEST_METHOD') == 'POST' and environ.get('CONTENT_TYPE', '').startswith('application/json'):
            try:
                length = int(environ.get('CONTENT_LENGTH') or 0)
                body_bytes = environ['wsgi.input'].read(length) if length > 0 else b''
                environ['wsgi.input'] = BytesIO(body_bytes)
                content = body_bytes.decode('utf-8', errors='ignore')
                if self.detector.detect_xss_patterns(content):
                    # 记录并返回拦截响应
                    self._log_attack(ip, content, blocked=True)
                    response_body = b'{"error": "XSS attack detected and blocked"}'
                    start_response('400 Bad Request', [
                        ('Content-Type', 'application/json; charset=utf-8'),
                        ('Content-Length', str(len(response_body)))
                    ])
                    return [response_body]
            except Exception as e:
                logging.exception("XSS middleware error")

        return self.app_wsgi(environ, start_response)