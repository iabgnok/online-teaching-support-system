#!/usr/bin/env python3
"""
清理 app.py 的智能脚本
保留：
  1. 所有导入 (除了 render_template 和 flash)
  2. Flask 应用初始化
  3. 数据库初始化
  4. 蓝图注册
  5. 助手函数 (generate_next_id 等)
  6. API 路由只保留关键的 API 部分
  7. 删除所有 @app.route 的服务端渲染路由

删除：
  1. render_template 导入
  2. 所有 @app.route 装饰的路由
  3. 所有 render_template(...) 调用
  4. 所有 flash(...) 调用和相关装饰器
"""

import re
import os

app_py_path = r'e:\online_teaching_support_system\app.py'

# 备份原始文件
backup_path = app_py_path + '.backup'
os.system(f'copy "{app_py_path}" "{backup_path}"')
print(f"✅ 已备份到: {backup_path}")

with open(app_py_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. 删除 render_template 导入
content = re.sub(
    r'from flask import .*?render_template.*?\n',
    lambda m: m.group(0).replace('render_template', '').replace(', ,', ',').rstrip() + '\n' if 'render_template' in m.group(0) else m.group(0),
    content
)

# 清理多余的逗号
content = re.sub(r', *,', ',', content)
content = re.sub(r'\(, *', '(', content)
content = re.sub(r', *\)', ')', content)

# 2. 删除所有包含 @app.route 的函数定义
# 这个比较复杂，需要找到完整的函数体

lines = content.split('\n')
new_lines = []
i = 0
skip_function = False
indent_level = 0

while i < len(lines):
    line = lines[i]
    
    # 检查是否是 @app.route 装饰器
    if re.match(r'^@app\.route\(', line):
        # 跳过这个装饰器及后续的函数定义
        skip_function = True
        i += 1
        continue
    
    # 检查是否是 @login_required 等装饰器（紧跟在 @app.route 后面）
    if skip_function and re.match(r'^@(login_required|role_required|admin_permission_required|login_manager|wraps)', line):
        i += 1
        continue
    
    # 如果需要跳过函数，检查函数定义行
    if skip_function and line.startswith('def '):
        # 记录函数的缩进级别
        indent_level = len(line) - len(line.lstrip())
        i += 1
        continue
    
    # 如果正在跳过函数，继续跳过直到回到前一个缩进级别
    if skip_function:
        current_indent = len(line) - len(line.lstrip())
        # 空行不算
        if line.strip():
            if current_indent <= indent_level and not line.startswith(' ' * (indent_level + 1)):
                # 函数结束了
                skip_function = False
            else:
                i += 1
                continue
        else:
            i += 1
            continue
    
    # 保留这一行
    new_lines.append(line)
    i += 1

content = '\n'.join(new_lines)

# 3. 删除 render_template(...) 的调用
# 这个很危险，我们只删除整行的情况
content = re.sub(r'^\s*return render_template\(.*?\)\s*$', '', content, flags=re.MULTILINE)

# 4. 删除 flash(...) 的调用
content = re.sub(r'\s*flash\([^)]*\)\s*\n?', '\n', content)

# 5. 删除空行（多个连续的空行变成一个）
content = re.sub(r'\n\n\n+', '\n\n', content)

# 保存清理后的文件
with open(app_py_path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"✅ app.py 清理完成")
print(f"📊 文件大小: {len(content)} 字符")
