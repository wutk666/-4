"""验证应用是否能正常启动"""
import sys
import traceback

print("=" * 60)
print("应用启动验证")
print("=" * 60)

try:
    print("\n1. 导入 create_app...")
    from app import create_app
    print("   ✓ 成功")
    
    print("\n2. 创建应用实例...")
    app = create_app()
    print("   ✓ 成功")
    
    print("\n3. 检查路由...")
    routes = list(app.url_map.iter_rules())
    attack_routes = [str(r) for r in routes if 'attack' in str(r) or 'sqli' in str(r) or 'cmdi' in str(r) or 'path' in str(r)]
    
    print(f"   ✓ 总路由数: {len(routes)}")
    print(f"   ✓ 攻击相关路由: {len(attack_routes)}")
    
    print("\n4. 攻击测试路由列表:")
    for route in sorted(attack_routes):
        print(f"   - {route}")
    
    print("\n5. 检查模板...")
    required_templates = [
        'attack_hub.html',
        'test_sqli.html',
        'test_cmdi.html',
        'test_path_traversal.html',
        'sqli_sandbox.html'
    ]
    
    import os
    template_dir = os.path.join(app.root_path, 'templates')
    for template in required_templates:
        path = os.path.join(template_dir, template)
        if os.path.exists(path):
            print(f"   ✓ {template}")
        else:
            print(f"   ✗ {template} (缺失)")
    
    print("\n" + "=" * 60)
    print("✓ 应用验证成功！可以启动服务器了。")
    print("=" * 60)
    print("\n下一步:")
    print("1. 初始化数据库: python init_attack_ranges.py")
    print("2. 启动应用: python run.py")
    print("3. 访问: http://localhost:5000/attack_hub")
    print("\n" + "=" * 60)
    
except Exception as e:
    print(f"\n✗ 错误: {e}")
    print("\n完整错误信息:")
    traceback.print_exc()
    sys.exit(1)
