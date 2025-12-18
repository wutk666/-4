from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.config.from_object('app.config.Config')

    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.jinja_env.auto_reload = True

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'login'

    with app.app_context():
        # 导入并创建模型表
        from . import models
        db.create_all()
        # 创建默认用户（仅用于测试 — 使用哈希密码）
        if not models.User.query.filter_by(username='admin').first():
            admin = models.User(username='admin')
            admin.set_password('admin')
            db.session.add(admin)
            db.session.commit()

    # 注册路由和中间件
    from .routes import init_routes
    init_routes(app)

    try:
        from .xss_security import XSSMiddleware
        app.wsgi_app = XSSMiddleware(app, app.wsgi_app)
    except Exception:
        pass

    return app