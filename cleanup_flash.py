#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
清理 flash 调用
"""
import re

def cleanup_flash():
    """清理app.py中的flash调用"""
    
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 删除所有 flash(...) 行
    # 匹配 flash(...) 并删除整行
    lines = content.split('\n')
    output_lines = []
    
    for line in lines:
        # 如果是纯粹的 flash(...) 调用，删除
        if re.match(r'^\s*flash\(', line.strip()):
            # 跳过这一行
            continue
        else:
            output_lines.append(line)
    
    content = '\n'.join(output_lines)
    
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print('✓ 已清理 flash 调用')

if __name__ == '__main__':
    cleanup_flash()
