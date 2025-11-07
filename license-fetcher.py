#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 Maven 仓库页面识别 jar 包的 license 并生成 license 文件
"""

import re
import sys
import os
import shutil
import requests
from lxml import etree

# 从 matcher.py 导入规则
single_license_rules = {
    "Apache 2.0": lambda license_name: "Apache" in license_name,
    "MIT": lambda license_name: "MIT" in license_name,
    "BSD-2-Clause": lambda license_name: "BSD" in license_name and "2" in license_name,
    "BSD-3-Clause": lambda license_name: "BSD" in license_name and "3" in license_name,
    "BSD": lambda license_name: "BSD" in license_name,
    "EPL 1.0": lambda license_name: ("EPL" in license_name or "Eclipse Public License" in license_name) and "1" in license_name,
    "EPL 2.0": lambda license_name: ("EPL" in license_name or "Eclipse Public License" in license_name) and "2" in license_name,
    "ISC": lambda license_name: "ISC" in license_name,
    "EDL 1.0": lambda license_name: ("EDL" in license_name or "Eclipse Distribution License" in license_name) and "1" in license_name,
    "CDDL 1.1": lambda license_name: "CDDL" in license_name and "1.1" in license_name,
    "CDDL": lambda license_name: "CDDL" in license_name,
    "CC0 1.0": lambda license_name: "Creative Commons CC0" in license_name,
    "Public Domain": lambda license_name: "Public Domain" in license_name,
}

def any_match(str):
    return lambda license_names: any(single_license_rules[str](name) for name in license_names)

multiple_license_rules = {
    "Apache 2.0": any_match("Apache 2.0"),
    "EDL 1.0": any_match("EDL 1.0"),
    "EPL 2.0": any_match("EPL 2.0"),
    "CC0 1.0": any_match("CC0 1.0"),
    "MIT": any_match("MIT"),
    "CDDL": any_match("CDDL"),
    "Public Domain": any_match("Public Domain"),
}

predefined_rules = {
    "json-20210307.jar": "Public Domain",
    "java-cup-runtime-11b-20160615.jar": "Historical Permission Notice and Disclaimer",
    "LatencyUtils-2.0.3.jar": "BSD-2-Clause",
    "jakarta.activation-2.0.0.jar": "BSD-3-Clause",
    "netty-tcnative-boringssl-static-2.0.36.Final.jar": "Apache 2.0",
    "netty-tcnative-classes-2.0.46.Final.jar": "Apache 2.0",
    "sjk-jfr5-0.5.jar": "Apache 2.0",
    "sjk-jfr6-0.7.jar": "Apache 2.0",
    "sjk-nps-0.9.jar": "Apache 2.0",
    "javassist-3.21.0-GA.jar": "Apache 2.0",
    "javassist-3.24.0-GA.jar": "Apache 2.0",
    "javassist-3.28.0-GA.jar": "Apache 2.0",
    "jersey-apache-connector-3.0.3.jar": "EPL 2.0",
    "jersey-client-3.0.3.jar": "EPL 2.0",
    "jersey-common-3.0.3.jar": "EPL 2.0",
    "jersey-container-grizzly2-http-3.0.3.jar": "EPL 2.0",
    "jersey-container-grizzly2-servlet-3.0.3.jar": "EPL 2.0",
    "jersey-container-servlet-3.0.3.jar": "EPL 2.0",
    "jersey-container-servlet-core-3.0.3.jar": "EPL 2.0",
    "jersey-entity-filtering-3.0.3.jar": "EPL 2.0",
    "jersey-hk2-3.0.3.jar": "EPL 2.0",
    "jersey-media-jaxb-3.0.3.jar": "EPL 2.0",
    "jersey-media-json-jackson-3.0.3.jar": "EPL 2.0",
    "jersey-server-3.0.3.jar": "EPL 2.0",
    "jersey-test-framework-core-3.0.3.jar": "EPL 2.0",
    "jersey-test-framework-provider-grizzly2-3.0.3.jar": "EPL 2.0"
}


def parse_input_line(line):
    """从输入行中提取 jar 包名和 URL"""
    # 匹配格式: Error: No matching rule for jar_name.jar https://...
    pattern = r'Error: No matching rule for ([^\s]+\.jar)\s+(https://[^\s,]+)'
    match = re.search(pattern, line)
    if match:
        jar_name = match.group(1)
        url = match.group(2)
        return jar_name, url
    return None, None


def fetch_license_from_maven(url):
    """从 Maven 仓库页面获取 license 信息"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # 解析 HTML
        html = etree.HTML(response.text)
        
        # 方法1: 从 POM 文件中提取
        pom_text = None
        pom_elements = html.xpath('//pre[@data-test="pom-file"]/text()')
        if pom_elements:
            pom_text = pom_elements[0]
        
        licenses = []
        if pom_text:
            try:
                root = etree.fromstring(pom_text.encode('utf-8'))
                namespaces = {'m': 'http://maven.apache.org/POM/4.0.0'}
                
                # 尝试带命名空间
                license_elements = root.findall('.//m:licenses/m:license', namespaces)
                for license_elem in license_elements:
                    name_elem = license_elem.find('m:name', namespaces)
                    if name_elem is not None and name_elem.text:
                        licenses.append(name_elem.text)
                
                # 尝试无命名空间
                if not licenses:
                    license_elements = root.findall('.//licenses/license')
                    for license_elem in license_elements:
                        name_elem = license_elem.find('name')
                        if name_elem is not None and name_elem.text:
                            licenses.append(name_elem.text)
            except Exception as e:
                pass
        
        # 方法2: 从页面元素中提取
        if not licenses:
            license_elements = html.xpath('//li[@data-test="license"]/text()')
            licenses = [elem.strip() for elem in license_elements if elem.strip()]
        
        return licenses
    except Exception as e:
        print(f"警告: 无法获取 {url} 的 license 信息: {e}", file=sys.stderr)
        return []


def match_license_type(jar_name, license_names):
    """匹配 license 类型"""
    # 检查预定义规则
    if jar_name in predefined_rules:
        return predefined_rules[jar_name]
    
    if not license_names:
        return None
    
    # 多个 license 的情况
    if len(license_names) >= 2:
        for rule_name, rule_logic in multiple_license_rules.items():
            if rule_logic(license_names):
                return rule_name
        return None
    
    # 单个 license 的情况
    if len(license_names) == 1:
        license_name = license_names[0]
        # 按优先级顺序匹配（更具体的规则在前）
        priority_order = [
            "Apache 2.0", "EPL 2.0", "EPL 1.0", "EDL 1.0", 
            "CDDL 1.1", "BSD-3-Clause", "BSD-2-Clause", 
            "CC0 1.0", "CDDL", "BSD", "MIT", "ISC", "Public Domain"
        ]
        for rule_name in priority_order:
            if rule_name in single_license_rules:
                if single_license_rules[rule_name](license_name):
                    return rule_name
    
    return None


def generate_license_file(jar_name, license_type):
    """根据模板生成 license 文件"""
    name = jar_name.split('.jar')[0]
    license_dest = f"licenses/LICENSE-{name}.txt"
    
    # 确保 licenses 目录存在
    os.makedirs('licenses', exist_ok=True)
    
    # 检查模板文件是否存在
    template_file = f"licenses-tpl/{license_type}.txt"
    if os.path.exists(template_file):
        shutil.copyfile(template_file, license_dest)
        return True
    else:
        # 如果模板不存在，创建一个空文件或包含 license 类型的文件
        with open(license_dest, 'w') as f:
            f.write(f"License: {license_type}\n")
        return False


def main():
    """主函数"""
    # 从标准输入读取
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    else:
        lines = sys.stdin.readlines()
    
    # 解析输入
    jar_urls = []
    for line in lines:
        jar_name, url = parse_input_line(line.strip())
        if jar_name and url:
            jar_urls.append((jar_name, url))
    
    if not jar_urls:
        print("未找到有效的 jar 包信息", file=sys.stderr)
        return
    
    # 处理每个 jar 包
    results = []
    for jar_name, url in jar_urls:
        print(f"正在处理: {jar_name}...", file=sys.stderr)
        
        # 获取 license 信息
        license_names = fetch_license_from_maven(url)
        
        # 匹配 license 类型
        license_type = match_license_type(jar_name, license_names)
        
        if license_type:
            # 生成 license 文件
            generate_license_file(jar_name, license_type)
            results.append((url, license_type))
        else:
            print(f"警告: 无法识别 {jar_name} ({url}) 的 license 类型", file=sys.stderr)
            print(f"  找到的 license 名称: {license_names}", file=sys.stderr)
    
    # 按字典序排序并输出结果
    results.sort(key=lambda x: x[0])
    for url, license_type in results:
        print(f"{url} -> {license_type}")


if __name__ == "__main__":
    main()

