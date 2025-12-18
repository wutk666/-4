"""检查所有注册的路由"""
from app import create_app

app = create_app()

print("=" * 80)
print("所有注册的路由")
print("=" * 80)

# 获取所有路由
routes = []
for rule in app.url_map.iter_rules():
    routes.append({
        'endpoint': rule.endpoint,
        'methods': ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'})),
        'path': str(rule)
    })

# 按路径排序
routes.sort(key=lambda x: x['path'])

# 显示所有路由
for route in routes:
    print(f"{route['methods']:10} {route['path']:50} -> {route['endpoint']}")

print("\n" + "=" * 80)
print("攻击测试相关路由")
print("=" * 80)

attack_routes = [r for r in routes if 'attack' in r['path'] or 'sqli' in r['path'] or 'cmdi' in r['path'] or 'path' in r['path']]
for route in attack_routes:
    print(f"{route['methods']:10} {route['path']:50} -> {route['endpoint']}")

print(f"\n总路由数: {len(routes)}")
print(f"攻击相关路由数: {len(attack_routes)}")
