#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re

api_dir = 'api/v1'
corrupted_chars = 'ćĺčşěĐħĩĭĮįĲĳĴĵĶķĸĹĻļĽľĿŀŁłŃńņŇňŉŊŋŌōŎŏŐőŒœŔŕŖŗŘřŚśŜŝŞşŠšŢţŤťŦŧŨũŪūŬŭŮůŰűŲųŴŵŶŷŸŹźŻż'

problematic_files = {}

for filename in sorted(os.listdir(api_dir)):
    if filename.endswith('.py'):
        filepath = os.path.join(api_dir, filename)
        
        # Try different encodings
        encodings_to_try = ['latin1', 'cp1252', 'iso-8859-1', 'utf-8']
        
        for encoding in encodings_to_try:
            try:
                with open(filepath, 'r', encoding=encoding) as f:
                    lines = f.readlines()
                
                problematic = []
                for line_num, line in enumerate(lines, 1):
                    if any(char in line for char in corrupted_chars):
                        problematic.append((line_num, line.rstrip()))
                
                if problematic:
                    problematic_files[filename] = {
                        'encoding': encoding,
                        'lines': problematic
                    }
                break
            except:
                continue

print('=' * 60)
print('API v1 文件编码问题检测结果')
print('=' * 60)
print()

if problematic_files:
    print(f'发现 {len(problematic_files)} 个文件存在编码问题:\n')
    
    for filename in sorted(problematic_files.keys()):
        info = problematic_files[filename]
        print(f'文件: api/v1/{filename}')
        print(f'  检测编码: {info["encoding"]}')
        print(f'  问题行数: {len(info["lines"])}')
        print(f'  问题行号: {", ".join(str(line[0]) for line in info["lines"][:10])}', end='')
        if len(info['lines']) > 10:
            print(f', ... 共{len(info["lines"])}行')
        else:
            print()
        print()
else:
    print('好消息: 未发现文件中存在损坏的中文字符')
