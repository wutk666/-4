"""
重置数据库 - 删除旧表并创建新表
"""
import os
from app import create_app, db

app = create_app()

with app.app_context():
    print("=" * 60)
    print("重置数据库")
    print("=" * 60)
    
    # 删除所有表
    print("\n1. 删除所有旧表...")
    db.drop_all()
    print("   ✓ 完成")
    
    # 创建所有新表
    print("\n2. 创建所有新表...")
    db.create_all()
    print("   ✓ 完成")
    
    # 创建默认管理员用户
    print("\n3. 创建默认管理员...")
    from app.models import User
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin')
        admin.set_password('admin')
        db.session.add(admin)
        db.session.commit()
        print("   ✓ 管理员账户已创建 (admin/admin)")
    else:
        print("   ✓ 管理员账户已存在")
    
    print("\n" + "=" * 60)
    print("✓ 数据库重置完成！")
    print("=" * 60)
    print("\n下一步:")
    print("1. 初始化靶场数据: python init_attack_ranges.py")
    print("2. 启动服务器: python run.py")
    print("\n" + "=" * 60)
