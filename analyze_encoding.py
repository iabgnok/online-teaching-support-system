#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
分析 api/v1 目录中的中文编码问题
"""

import os

def analyze_encoding_issues():
    api_dir = 'api/v1'
    
    print('=' * 80)
    print('API v1 文件中文编码问题完整分析报告')
    print('=' * 80)
    print()
    
    # 扫描所有 Python 文件
    files_analysis = {}
    
    for filename in sorted(os.listdir(api_dir)):
        if filename.endswith('.py'):
            filepath = os.path.join(api_dir, filename)
            
            with open(filepath, 'rb') as f:
                raw_bytes = f.read()
            
            # 尝试 UTF-8 解码
            utf8_valid = False
            utf8_has_chinese = False
            try:
                utf8_content = raw_bytes.decode('utf-8')
                utf8_valid = True
                # 检查是否有中文字符
                utf8_has_chinese = any('\u4e00' <= char <= '\u9fff' for char in utf8_content)
            except:
                pass
            
            # 尝试 Latin-1 解码
            latin1_content = raw_bytes.decode('latin1')
            
            # 检查用 Latin-1 解码后是否会出现损坏的特殊字符
            corrupted_chars = set('ćĺčşěĐħĩĭĮįĲĳĴĵĶķĸĹĻļĽľĿŀŁłŃńņŇňŉŊŋŌōŎŏŐőŒœŔŕŖŗŘřŚśŜŝŞşŠšŢţŤťŦŧŨũŪūŬŭŮůŰűŲųŴŵŶŷŸŹźŻż')
            has_corrupted = any(char in latin1_content for char in corrupted_chars)
            
            files_analysis[filename] = {
                'utf8_valid': utf8_valid,
                'utf8_has_chinese': utf8_has_chinese,
                'has_corrupted_when_latin1': has_corrupted,
                'size_kb': len(raw_bytes) / 1024
            }
    
    # 输出分析结果
    print('1. 文件编码总览:')
    print('-' * 80)
    print(f'{"文件名":<25} {"UTF-8有效":<12} {"含中文":<12} {"Latin-1显示损坏":<18} {"大小(KB)":<10}')
    print('-' * 80)
    
    problematic_files = []
    
    for filename in sorted(files_analysis.keys()):
        info = files_analysis[filename]
        
        utf8_status = '✓ 是' if info['utf8_valid'] else '✗ 否'
        chinese_status = '✓ 有' if info['utf8_has_chinese'] else '✗ 无'
        corrupted_status = '✓ 是' if info['has_corrupted_when_latin1'] else '✗ 否'
        
        print(f'{filename:<25} {utf8_status:<12} {chinese_status:<12} {corrupted_status:<18} {info["size_kb"]:<10.1f}')
        
        if info['has_corrupted_when_latin1'] and info['utf8_valid']:
            problematic_files.append(filename)
    
    print()
    print('2. 问题文件详情:')
    print('-' * 80)
    
    if problematic_files:
        print(f'\n发现 {len(problematic_files)} 个文件存在中文编码问题:\n')
        
        for filename in problematic_files:
            filepath = os.path.join(api_dir, filename)
            
            with open(filepath, 'rb') as f:
                raw_bytes = f.read()
            
            # 用 UTF-8 解码获取正确的中文内容
            utf8_content = raw_bytes.decode('utf-8')
            lines = utf8_content.split('\n')
            
            # 找出包含中文的行
            chinese_lines = []
            for line_num, line in enumerate(lines, 1):
                if any('\u4e00' <= char <= '\u9fff' for char in line):
                    chinese_lines.append((line_num, line.strip()))
            
            print(f'文件: api/v1/{filename}')
            print(f'  当前编码: UTF-8 (文件头可能标记为其他编码)')
            print(f'  含有中文行数: {len(chinese_lines)}')
            
            if chinese_lines:
                print(f'  中文出现的行号: {[line[0] for line in chinese_lines]}')
                print(f'  中文内容示例:')
                for line_num, content in chinese_lines[:3]:
                    display_content = content[:70] + '...' if len(content) > 70 else content
                    print(f'    行 {line_num}: {display_content}')
                if len(chinese_lines) > 3:
                    print(f'    ... 共 {len(chinese_lines)} 行包含中文')
            print()
    else:
        print('未发现问题')
    
    print('=' * 80)
    print('总结:')
    print('-' * 80)
    print(f'总文件数: {len(files_analysis)}')
    print(f'UTF-8 编码的文件: {sum(1 for f in files_analysis.values() if f["utf8_valid"])}')
    print(f'包含中文的文件: {sum(1 for f in files_analysis.values() if f["utf8_has_chinese"])}')
    print(f'潜在编码问题的文件: {len(problematic_files)}')
    print()
    
    if problematic_files:
        print('建议:')
        print('这些文件使用正确的 UTF-8 编码存储了中文内容，但可能被某些编辑器')
        print('或系统标记为其他编码格式（如 Latin-1）。当以错误的编码打开时，')
        print('中文字符会显示为损坏的特殊字符（如 ć、ĺ、č 等）。')
        print()
        print('建议的解决方案:')
        print('1. 在 VS Code 中为这些文件明确设置 UTF-8 编码')
        print('2. 重新保存文件以确保编码正确')
        print('3. 或者，使用修复脚本重新编码这些文件')
    
    return problematic_files

if __name__ == '__main__':
    analyze_encoding_issues()
