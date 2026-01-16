#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
清理旧的HTML模板引用脚本
"""
import re

def cleanup_app_py():
    """清理app.py中的render_template调用"""
    
    with open('app.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    output_lines = []
    skip_next = False
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # 如果行包含 render_template，替换为 redirect('/')
        if 'render_template(' in line:
            # 获取缩进
            indent = len(line) - len(line.lstrip())
            output_lines.append(' ' * indent + "return redirect('/')\n")
            
            # 跳过到下一行直到找到闭合括号
            while i < len(lines) - 1 and ')' not in line:
                i += 1
                line = lines[i]
        else:
            output_lines.append(line)
        
        i += 1
    
    with open('app.py', 'w', encoding='utf-8') as f:
        f.writelines(output_lines)
    
    print('✓ 已清理 app.py 中的 render_template 调用')

if __name__ == '__main__':
    cleanup_app_py()
