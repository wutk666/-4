"""修复 routes.py 文件中的重复代码和缩进问题"""

# 读取文件
with open('app/routes.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 找到重复的 sqli_reset 函数（第二个）和错误的缩进
fixed_lines = []
skip_until = -1
found_duplicate = False

for i, line in enumerate(lines):
    # 跳过重复的 sqli_reset 函数 (行601-619)
    if i >= 600 and i <= 619 and not found_duplicate:
        if '@app.route(\'/attack/sqli/reset\'' in line:
            found_duplicate = True
            skip_until = i + 19  # 跳过整个函数
            continue
    
    if i <= skip_until:
        continue
    
    # 修复缩进问题 (行622-673的函数应该在 init_routes 内)
    if i >= 621 and i < 674:
        # 这些行需要增加缩进
        if line.startswith('@app.route') or line.startswith('def '):
            fixed_lines.append('    ' + line)
        elif line.strip() and not line.startswith(' '):
            fixed_lines.append('    ' + line)
        else:
            fixed_lines.append(line)
    # 修复 path_view 函数的缩进 (行675开始)
    elif i >= 674 and 'def path_view' in line:
        fixed_lines.append('    @app.route(\'/attack/path/view\', methods=[\'POST\'])\n')
        fixed_lines.append('    def path_view():\n')
        skip_until = i + 1
    else:
        fixed_lines.append(line)

# 写回文件
with open('app/routes.py', 'w', encoding='utf-8') as f:
    f.writelines(fixed_lines)

print("✓ routes.py 文件已修复")
print("- 删除了重复的 sqli_reset 函数")
print("- 修复了缩进问题")
