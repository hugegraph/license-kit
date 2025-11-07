#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将新的 license 信息合并到 LICENSE 文件中
"""

import re
import sys
from collections import defaultdict


def parse_new_entries(lines):
    """解析新的 license 条目"""
    entries = []
    for line in lines:
        line = line.strip()
        if not line or not '->' in line:
            continue
        
        # 解析格式: {url} -> {license type}
        parts = line.split('->', 1)
        if len(parts) == 2:
            url = parts[0].strip()
            license_type = parts[1].strip()
            entries.append((url, license_type))
    
    return entries


def parse_existing_license_file(file_path):
    """解析现有的 LICENSE 文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 按 license 类型分组
    license_sections = {}
    current_license_type = None
    current_entries = []
    
    i = 0
    while i < len(lines):
        line = lines[i].rstrip('\n')
        
        # 检测 license 类型标题
        # 格式: Third party {license type} licenses
        match = re.match(r'^Third party (.+?) licenses$', line)
        if match:
            # 保存之前的 section
            if current_license_type:
                license_sections[current_license_type] = current_entries.copy()
            
            # 开始新的 section
            current_license_type = match.group(1)
            current_entries = []
            # 跳过接下来的分隔线和描述行
            i += 1
            # 跳过分隔线（如果存在）
            if i < len(lines) and '=' * 72 in lines[i]:
                i += 1
            # 跳过描述行
            while i < len(lines):
                line_content = lines[i].strip()
                if not line_content or 'The following components' in line_content or 'The text of each license' in line_content:
                    i += 1
                else:
                    break
            continue
        
        # 解析条目: "    {url} -> {license type}"
        if current_license_type and '->' in line:
            # 匹配格式: "    {url} -> {license type}"
            match = re.match(r'^\s+(.+?)\s+->\s+(.+?)$', line)
            if match:
                url = match.group(1).strip()
                license_type = match.group(2).strip()
                current_entries.append((url, license_type))
        
        i += 1
    
    # 保存最后一个 section
    if current_license_type:
        license_sections[current_license_type] = current_entries
    
    return license_sections


def merge_entries(existing_entries, new_entries):
    """合并条目，去重并按字典序排序"""
    # 使用 set 来去重（基于 URL）
    url_set = set()
    merged = []
    
    # 先添加现有的条目
    for url, license_type in existing_entries:
        if url not in url_set:
            url_set.add(url)
            merged.append((url, license_type))
    
    # 再添加新条目
    for url, license_type in new_entries:
        if url not in url_set:
            url_set.add(url)
            merged.append((url, license_type))
    
    # 按 URL 字典序排序
    merged.sort(key=lambda x: x[0])
    
    return merged


def generate_license_file(license_sections, output_file):
    """生成合并后的 LICENSE 文件"""
    # 定义 license 类型的顺序（按现有文件中的顺序）
    license_order = [
        "CC0 1.0",
        "BSD-2-Clause",
        "Apache 2.0",
        "BSD",
        "MIT",
        "EPL 2.0",
        "BSD-3-Clause",
        "EDL 1.0",
        "Historical Permission Notice and Disclaimer",
        "CDDL",
        "CDDL 1.1",
        "ISC",
        "EPL 1.0",
        "Public Domain",
    ]
    
    # 收集所有 license 类型
    all_license_types = set(license_sections.keys())
    
    # 对于不在预定义顺序中的 license 类型，按字母序添加到末尾
    other_licenses = sorted(all_license_types - set(license_order))
    final_order = license_order + other_licenses
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for license_type in final_order:
            if license_type not in license_sections:
                continue
            
            entries = license_sections[license_type]
            if not entries:
                continue
            
            # 写入 section 标题
            f.write('=' * 72 + '\n')
            f.write(f'Third party {license_type} licenses\n')
            f.write('=' * 72 + '\n')
            f.write(f'The following components are provided under the {license_type} License. See project link for details.\n')
            f.write('The text of each license is also included in licenses/LICENSE-[project].txt.\n\n')
            
            # 写入条目
            for url, _ in entries:
                f.write(f'    {url} -> {license_type}\n')
            
            f.write('\n')


def main():
    """主函数"""
    if len(sys.argv) < 3:
        print("用法: python3 merge-license.py <新条目文件> <LICENSE文件> [输出文件]")
        print("  或: python3 merge-license.py - <LICENSE文件> [输出文件]  # 从标准输入读取")
        sys.exit(1)
    
    input_source = sys.argv[1]
    license_file = sys.argv[2]
    output_file = sys.argv[3] if len(sys.argv) > 3 else license_file
    
    # 读取新条目
    if input_source == '-':
        new_lines = sys.stdin.readlines()
    else:
        with open(input_source, 'r', encoding='utf-8') as f:
            new_lines = f.readlines()
    
    new_entries = parse_new_entries(new_lines)
    print(f"解析到 {len(new_entries)} 个新条目", file=sys.stderr)
    
    # 解析现有 LICENSE 文件
    existing_sections = parse_existing_license_file(license_file)
    print(f"现有 LICENSE 文件包含 {len(existing_sections)} 个 license 类型", file=sys.stderr)
    
    # 合并条目
    merged_sections = {}
    for license_type, entries in existing_sections.items():
        # 获取该类型的新条目
        new_entries_for_type = [e for e in new_entries if e[1] == license_type]
        merged_sections[license_type] = merge_entries(entries, new_entries_for_type)
        if new_entries_for_type:
            print(f"  {license_type}: 现有 {len(entries)} 条，新增 {len(new_entries_for_type)} 条，合并后 {len(merged_sections[license_type])} 条", file=sys.stderr)
    
    # 处理新 license 类型
    existing_types = set(existing_sections.keys())
    new_types = set(e[1] for e in new_entries) - existing_types
    for license_type in new_types:
        new_entries_for_type = [e for e in new_entries if e[1] == license_type]
        merged_sections[license_type] = sorted(new_entries_for_type, key=lambda x: x[0])
        print(f"  新类型 {license_type}: {len(new_entries_for_type)} 条", file=sys.stderr)
    
    # 生成合并后的文件
    generate_license_file(merged_sections, output_file)
    print(f"\n合并完成，结果已写入: {output_file}", file=sys.stderr)


if __name__ == "__main__":
    main()

