from datetime import datetime
from . import db
from flask_login import UserMixin

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)  # 测试用途：明文/哈希兼容

    def set_password(self, pwd: str):
        from werkzeug.security import generate_password_hash
        self.password = generate_password_hash(pwd)

    def check_password(self, pwd: str) -> bool:
        from werkzeug.security import check_password_hash
        try:
            return check_password_hash(self.password, pwd)
        except Exception:
            return self.password == pwd

class AttackLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip = db.Column(db.String(45), nullable=False)
    payload = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    blocked = db.Column(db.Boolean, default=True)
    attack_type = db.Column(db.String(50), default='xss')  # xss, sqli, cmdi, path_traversal, brute_force, dos
    attack_category = db.Column(db.String(50), default='injection')  # injection, access_control, behavioral
    severity = db.Column(db.String(20), default='medium')  # low, medium, high, critical
    target_url = db.Column(db.String(500), nullable=True)  # 攻击目标URL
    user_agent = db.Column(db.String(500), nullable=True)  # User-Agent信息

class BannedIP(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip = db.Column(db.String(45), unique=True, nullable=False)
    banned_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)  # 可选：临时封禁失效时间
    permanent = db.Column(db.Boolean, default=False)

class Setting(db.Model):
    """简单的键值设置（用于持久化防御开关等）"""
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.String(500), nullable=True)

class Comment(db.Model):
    """存储型 XSS 演示用的评论模型"""
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(100), default='匿名')
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class RateLimitLog(db.Model):
    """频率限制日志，用于检测暴力破解和DoS攻击"""
    id = db.Column(db.Integer, primary_key=True)
    ip = db.Column(db.String(45), nullable=False, index=True)
    endpoint = db.Column(db.String(200), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    request_count = db.Column(db.Integer, default=1)

class AuthLoginAttempt(db.Model):
    """认证相关的登录尝试记录（用于暴力破解/撞库检测）"""
    id = db.Column(db.Integer, primary_key=True)
    ip = db.Column(db.String(45), nullable=False, index=True)
    username = db.Column(db.String(80), nullable=False, index=True)
    success = db.Column(db.Boolean, default=False, index=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    user_agent = db.Column(db.String(500), nullable=True)

class VulnerableUser(db.Model):
    """SQL注入靶场的模拟用户数据"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class VulnerableFile(db.Model):
    """目录遍历靶场的模拟文件记录"""
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    filepath = db.Column(db.String(500), nullable=False)
    content = db.Column(db.Text, nullable=True)
    is_sensitive = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)