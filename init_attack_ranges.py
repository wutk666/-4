"""
初始化攻击靶场数据库
创建测试用的靶场数据，包括SQL注入、目录遍历等场景的示例数据
"""
from app import create_app, db
from app.models import VulnerableUser, VulnerableFile
from datetime import datetime

def init_sqli_range():
    """初始化SQL注入靶场数据"""
    print("初始化 SQL 注入靶场...")
    
    # 清空现有数据
    VulnerableUser.query.delete()
    
    # 创建示例用户
    users = [
        VulnerableUser(
            username='admin',
            email='admin@example.com',
            password='admin123',
            role='admin'
        ),
        VulnerableUser(
            username='alice',
            email='alice@example.com',
            password='alice2024',
            role='user'
        ),
        VulnerableUser(
            username='bob',
            email='bob@example.com',
            password='bob@secure',
            role='user'
        ),
        VulnerableUser(
            username='charlie',
            email='charlie@example.com',
            password='charlie99',
            role='user'
        ),
        VulnerableUser(
            username='david',
            email='david@example.com',
            password='david_pwd',
            role='user'
        ),
        VulnerableUser(
            username='eve',
            email='eve@example.com',
            password='eve_secret',
            role='user'
        ),
        VulnerableUser(
            username='frank',
            email='frank@example.com',
            password='frank2024!',
            role='user'
        ),
        VulnerableUser(
            username='grace',
            email='grace@example.com',
            password='grace_pass',
            role='moderator'
        ),
    ]
    
    for user in users:
        db.session.add(user)
    
    db.session.commit()
    print(f"✓ 创建了 {len(users)} 个测试用户")

def init_path_traversal_range():
    """初始化目录遍历靶场数据"""
    print("初始化目录遍历靶场...")
    
    # 清空现有数据
    VulnerableFile.query.delete()
    
    # 创建示例文件记录
    files = [
        VulnerableFile(
            filename='readme.txt',
            filepath='documents/readme.txt',
            content='Welcome to our application!\n\nThis is a sample readme file.\n\nFeatures:\n- User management\n- File upload\n- Secure authentication',
            is_sensitive=False
        ),
        VulnerableFile(
            filename='guide.pdf',
            filepath='documents/guide.pdf',
            content='[PDF Content] User Guide - Version 1.0\n\nTable of Contents:\n1. Introduction\n2. Getting Started\n3. Advanced Features',
            is_sensitive=False
        ),
        VulnerableFile(
            filename='logo.png',
            filepath='images/logo.png',
            content='[PNG Image Data - Binary Content]',
            is_sensitive=False
        ),
        VulnerableFile(
            filename='index.html',
            filepath='public/index.html',
            content='<!DOCTYPE html>\n<html>\n<head><title>Home</title></head>\n<body><h1>Welcome</h1></body>\n</html>',
            is_sensitive=False
        ),
        VulnerableFile(
            filename='passwd',
            filepath='/etc/passwd',
            content='root:x:0:0:root:/root:/bin/bash\ndaemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin\nbin:x:2:2:bin:/bin:/usr/sbin/nologin\nsys:x:3:3:sys:/dev:/usr/sbin/nologin\nadmin:x:1000:1000:Admin User:/home/admin:/bin/bash',
            is_sensitive=True
        ),
        VulnerableFile(
            filename='shadow',
            filepath='/etc/shadow',
            content='root:$6$randomsalt$hashedpassword:18000:0:99999:7:::\nadmin:$6$randomsalt$hashedpassword:18000:0:99999:7:::',
            is_sensitive=True
        ),
        VulnerableFile(
            filename='config.php',
            filepath='config/config.php',
            content='<?php\n$db_host = "localhost";\n$db_user = "root";\n$db_pass = "secretpassword123";\n$db_name = "webapp";\n?>',
            is_sensitive=True
        ),
        VulnerableFile(
            filename='id_rsa',
            filepath='/home/admin/.ssh/id_rsa',
            content='-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQEA... [Private Key Content]\n-----END RSA PRIVATE KEY-----',
            is_sensitive=True
        ),
    ]
    
    for file in files:
        db.session.add(file)
    
    db.session.commit()
    print(f"✓ 创建了 {len(files)} 个测试文件记录")

def main():
    """主函数"""
    print("=" * 60)
    print("攻击靶场数据库初始化")
    print("=" * 60)
    
    app = create_app()
    
    with app.app_context():
        # 创建所有表
        print("\n创建数据库表...")
        db.create_all()
        print("✓ 数据库表创建完成")
        
        # 初始化各个靶场
        print("\n" + "=" * 60)
        init_sqli_range()
        
        print("\n" + "=" * 60)
        init_path_traversal_range()
        
        print("\n" + "=" * 60)
        print("✓ 所有靶场数据初始化完成！")
        print("=" * 60)
        
        print("\n靶场访问地址:")
        print("  - 攻击测试中心: http://localhost:5000/attack_hub")
        print("  - SQL 注入靶场: http://localhost:5000/test_sqli")
        print("  - 命令注入靶场: http://localhost:5000/test_cmdi")
        print("  - 目录遍历靶场: http://localhost:5000/test_path_traversal")
        print("\n" + "=" * 60)

if __name__ == '__main__':
    main()
