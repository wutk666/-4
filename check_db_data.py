"""检查靶场数据库是否有数据"""
from app import create_app, db
from app.models import VulnerableUser

app = create_app()

with app.app_context():
    users = VulnerableUser.query.all()
    print(f"靶场数据库中的用户数量: {len(users)}")
    
    if users:
        print("\n用户列表:")
        for u in users:
            print(f"  - ID: {u.id}, 用户名: {u.username}, 邮箱: {u.email}, 角色: {u.role}")
    else:
        print("\n⚠️ 靶场数据库为空！需要初始化数据。")
        print("\n请运行: python init_attack_ranges.py")
