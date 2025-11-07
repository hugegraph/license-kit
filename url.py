import json
import re

prefix = "https://central.sonatype.com/artifact"

pre_defined = {
    "jffi-1.2.16-native.jar": [(None, None, f"{prefix}/com.github.jnr/jffi/1.2.16")],
    "hanlp-portable-1.8.3.jar": [(None, None, f"{prefix}/com.hankcs/hanlp/portable-1.8.3")],
    "groovy-2.5.14-indy.jar": [(None, None, f"{prefix}/org.codehaus.groovy/groovy/2.5.14")],
    "groovy-groovysh-2.5.14-indy.jar": [(None, None, f"{prefix}/org.codehaus.groovy/groovy-groovysh/2.5.14")],
    "groovy-json-2.5.14-indy.jar": [(None, None, f"{prefix}/org.codehaus.groovy/groovy-json/2.5.14")],
    "groovy-jsr223-2.5.14-indy.jar": [(None, None, f"{prefix}/org.codehaus.groovy/groovy-jsr223/2.5.14")],
}


def extract_artifact_version(line):
    """
    从类似 accessors-smart-1.2.jar 的字符串中提取 artifactId 和 version
    只要满足 - 后面是数字的条件，即考虑匹配
    """
    line = line.strip()

    if line in pre_defined:
        return pre_defined[line]

    # 去除后缀 .jar（如果有）
    if line.endswith(".jar"):
        line = line[:-4]

    results = []

    # 从左到右查找所有符合条件的 -
    for i in range(len(line)):
        if line[i] == '-' and i + 1 < len(line) and line[i + 1].isdigit():
            artifact_id = line[:i]  # `-` 前面的部分
            version = line[i + 1:]  # `-` 后面的部分
            results.append((artifact_id, version, None))

    return results if results else [(None, None, None)]


def find_group_id_in_tree(artifact, version, tree_lines):
    """
    在 Maven dependency:tree 的输出中查找 groupId
    """
    search_pattern = f"{artifact}:jar:{version}"
    for line in tree_lines:
        if search_pattern in line:
            # 匹配到类似 [INFO] |  |  \- net.minidev:accessors-smart:jar:1.2:compile 的行
            group_id_match = re.search(r'(\S+):' + re.escape(artifact) + r':jar:' + re.escape(version), line)
            if group_id_match:
                return group_id_match.group(1)
    return None


def generate_maven_url(group_id, artifact, version):
    """
    根据 groupId, artifactId 和 version 生成 Maven Repository URL
    """
    return f"{prefix}/{group_id}/{artifact}/{version}"


def process_files(artifact_file, tree_file):
    """
    处理输入的两个文件，输出 Maven URL 到 urls.json 文件
    """
    # 读取 artifact 文件
    with open(artifact_file, 'r') as af:
        artifact_lines = af.readlines()

    # 读取 dependency tree 文件
    with open(tree_file, 'r') as tf:
        tree_lines = tf.readlines()

    # 准备输出数据
    output_data = []

    # 处理每个 artifact
    for line in artifact_lines:
        line = line.strip()  # 去掉行首尾空白字符
        found = False
        for (artifact, version, maven_url) in extract_artifact_version(line):
            if found:
                break
            if maven_url:
                output_data.append({"jar": line, "url": maven_url})  # 添加到输出列表
                found = True
                continue
            group_id = find_group_id_in_tree(artifact, version, tree_lines)
            if group_id:
                maven_url = generate_maven_url(group_id, artifact, version)
                output_data.append({"jar": line, "url": maven_url})  # 添加到输出列表
                found = True
        if not found:
            output_data.append({"jar": line, "url": "Error: Not found"})  # 处理未找到的情况

    # 将输出数据写入 JSON 文件
    with open('urls.json', 'w') as output_file:
        json.dump(output_data, output_file, indent=4)

# 示例调用
artifacts_path = "/Users/pengjunzhi/Code/hugegraph/install-dist/scripts/dependency/known-dependencies.txt"
dependency_tree_path = "/Users/pengjunzhi/Code/hugegraph/dependency-tree.txt"

process_files(artifacts_path, dependency_tree_path)

# input: known-dependencies.txt and dependency-tree output
# output: urls.json
