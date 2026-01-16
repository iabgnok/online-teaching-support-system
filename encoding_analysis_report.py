#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
API v1 中文编码问题完整分析报告
"""

import os

def find_corrupted_lines_in_file(filepath, filename):
    """查找文件中损坏的中文字符行"""
    
    with open(filepath, 'rb') as f:
        raw_bytes = f.read()
    
    # 用 Latin-1 解码（总是可以成功）
    latin1_content = raw_bytes.decode('latin1')
    lines = latin1_content.split('\n')
    
    # 这些特殊字符代表损坏的中文
    corrupted_chars = set('ćĺčşěĐħĩĭĮįĲĳĴĵĶķĸĹĻļĽľĿŀŁłŃńņŇňŉŊŋŌōŎŏŐőŒœŔŕŖŗŘřŚśŜŝŞşŠšŢţŤťŦŧŨũŪūŬŭŮůŰűŲųŴŵŶŷŸŹźŻż')
    
    problem_lines = []
    for line_num, line in enumerate(lines, 1):
        if any(char in line for char in corrupted_chars):
            problem_lines.append((line_num, line.strip()))
    
    return problem_lines

def main():
    api_dir = 'api/v1'
    
    print('=' * 90)
    print('在线教学支持系统 - API v1 模块中文编码问题分析报告')
    print('=' * 90)
    print()
    print('报告时间: 2026年1月16日')
    print('分析范围: api/v1 目录下所有 Python 文件')
    print()
    
    # 扫描所有文件
    files_with_issues = {}
    all_files_info = {}
    
    for filename in sorted(os.listdir(api_dir)):
        if filename.endswith('.py'):
            filepath = os.path.join(api_dir, filename)
            
            with open(filepath, 'rb') as f:
                raw_bytes = f.read()
            
            # 检查 UTF-8 有效性
            utf8_valid = False
            utf8_error_pos = None
            try:
                raw_bytes.decode('utf-8')
                utf8_valid = True
            except UnicodeDecodeError as e:
                utf8_error_pos = (e.start, e.end)
            
            # 查找损坏的行
            problem_lines = find_corrupted_lines_in_file(filepath, filename)
            
            all_files_info[filename] = {
                'size': len(raw_bytes),
                'utf8_valid': utf8_valid,
                'utf8_error_pos': utf8_error_pos,
                'problems': problem_lines
            }
            
            if problem_lines:
                files_with_issues[filename] = problem_lines
    
    # 第一部分：问题文件列表
    print('【第一部分】问题文件统计')
    print('-' * 90)
    print()
    
    total_files = len(all_files_info)
    problem_file_count = len(files_with_issues)
    total_problem_lines = sum(len(lines) for lines in files_with_issues.values())
    
    print(f'总文件数: {total_files}')
    print(f'有编码问题的文件: {problem_file_count}')
    print(f'总问题行数: {total_problem_lines}')
    print()
    
    if files_with_issues:
        print('问题文件清单:')
        print()
        
        for i, (filename, problem_lines) in enumerate(sorted(files_with_issues.items()), 1):
            print(f'{i}. api/v1/{filename}')
            print(f'   - 大小: {all_files_info[filename]["size"] / 1024:.1f} KB')
            print(f'   - UTF-8编码有效性: {"✓ 是" if all_files_info[filename]["utf8_valid"] else "✗ 否"}')
            print(f'   - 问题行数: {len(problem_lines)}')
            print(f'   - 问题行号: {[line[0] for line in problem_lines]}')
            
            # 显示前几行的内容
            print(f'   - 问题内容示例:')
            for line_num, content in problem_lines[:3]:
                display = content[:75] + '...' if len(content) > 75 else content
                print(f'       行 {line_num}: {display}')
            if len(problem_lines) > 3:
                print(f'       ... 还有 {len(problem_lines) - 3} 行')
            print()
    else:
        print('未发现任何文件存在中文编码问题！')
        print()
    
    # 第二部分：全面扫描结果
    print()
    print('【第二部分】全部文件编码状态')
    print('-' * 90)
    print()
    
    print(f'{"文件名":<25} {"大小(KB)":<12} {"UTF-8有效":<12} {"问题行数":<12}')
    print('-' * 90)
    
    for filename in sorted(all_files_info.keys()):
        info = all_files_info[filename]
        size_kb = info['size'] / 1024
        utf8_status = '✓ 是' if info['utf8_valid'] else '✗ 否'
        problem_count = len(info['problems'])
        problem_status = f'{problem_count} 行' if problem_count > 0 else '无'
        
        print(f'{filename:<25} {size_kb:<12.1f} {utf8_status:<12} {problem_status:<12}')
    
    print()
    
    # 第三部分：问题原因分析
    print('【第三部分】问题原因分析')
    print('-' * 90)
    print()
    
    if files_with_issues:
        print('根据分析，以下文件存在编码问题:')
        print()
        
        for filename in sorted(files_with_issues.keys()):
            info = all_files_info[filename]
            print(f'● {filename}')
            
            if not info['utf8_valid']:
                error_pos = info['utf8_error_pos']
                print(f'  - UTF-8 编码在字节位置 {error_pos[0]}-{error_pos[1]} 处出现无效字符')
                print(f'  - 可能原因: 文件混合了不同编码，或被用错误的编码编辑过')
            
            print(f'  - 当用 Latin-1 编码打开时，中文部分会显示为: ćĺčşěĐħĩĭĮį...')
            print()
    
    # 第四部分：建议方案
    print('【第四部分】修复建议')
    print('-' * 90)
    print()
    
    if files_with_issues:
        print('这些文件存在混合编码或编码标识错误的问题。建议的解决方案:')
        print()
        print('1. 方案一: 使用 VS Code 自动修复')
        print('   - 打开问题文件')
        print('   - 点击右下角编码指示器，选择 "通过编码重新打开"')
        print('   - 选择正确的编码（通常是 UTF-8）后重新保存')
        print()
        print('2. 方案二: 使用转换脚本')
        print('   - 运行修复脚本来自动纠正文件编码')
        print()
        print('3. 方案三: 手动检查和修复')
        print('   - 在代码编辑器中找到显示损坏的行')
        print('   - 替换为正确的中文注释')
        print()
    else:
        print('所有文件编码正常，无需修复！')
        print()
    
    # 第五部分：问题文件的详细列表
    if files_with_issues:
        print()
        print('【第五部分】问题文件的详细行号列表')
        print('-' * 90)
        print()
        
        for filename in sorted(files_with_issues.keys()):
            print(f'文件: api/v1/{filename}')
            print(f'问题行号: {[line[0] for line in files_with_issues[filename]]}')
            print()
    
    print('=' * 90)
    print('报告结束')
    print('=' * 90)

if __name__ == '__main__':
    main()
