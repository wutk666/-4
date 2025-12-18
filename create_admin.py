from app import create_app, db
from app.models import User, AuthLoginAttempt

app = create_app()
with app.app_context():
    users = User.query.all()
    print("当前用户：", [(u.id, u.username, u.password[:30] + ('...' if len(u.password)>30 else '')) for u in users])

    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin')
        admin.set_password('admin')
        db.session.add(admin)
        db.session.commit()
        print("已创建 admin / admin")
    else:
        admin.set_password('admin')
        db.session.commit()
        print("已重置 admin 密码为 admin")

    try:
        AuthLoginAttempt.query.filter_by(username='admin').delete()
        db.session.commit()
        print("已清空 admin 登录尝试记录")
    except Exception as e:
        db.session.rollback()
        print("清空登录尝试记录失败：", str(e))