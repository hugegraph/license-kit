import json
import os
import shutil
import zipfile
import tempfile
from collections import defaultdict


def extract_license(jar_path, jar_name, rule, license_url):
    # Create temporary directory for extraction
    with tempfile.TemporaryDirectory() as tmpdirname:
        name = jar_name.split('.jar')[0]
        extract_path = os.path.join(tmpdirname, name)
        license_dest = f"licenses/LICENSE-{name}.txt"

        # Try to find predefined license file
        predefined_license_file = f"licenses-predefined/{name}.txt"
        if os.path.exists(predefined_license_file):
            shutil.copyfile(predefined_license_file, license_dest)
            return f"from predefined license: {predefined_license_file}"

        # Unzip JAR file using zipfile
        with zipfile.ZipFile(jar_path, 'r') as jar_file:
            jar_file.extractall(extract_path)

        # Recursively find license files
        license_files = []
        for root, dirs, files in os.walk(extract_path):
            for file in files:
                if 'license' in file.lower():
                    license_files.append(os.path.join(root, file))

        # If license file is found in JAR, copy it
        if license_files:
            license_src = license_files[0]
            shutil.copyfile(license_src, license_dest)
            return "extracted from JAR"

        # Handle cases where no file is found in JAR
        if rule != "Apache 2.0" and license_url:
            with open(license_dest, 'w') as f:
                f.write(f"{license_url}\n")
            return f"from license_url: {license_url}"
        else:
            template_file = f"licenses-tpl/{rule}.txt"
            if os.path.exists(template_file):
                shutil.copyfile(template_file, license_dest)
                return f"from template file: {template_file}"

    return "no license found"


def process_licenses(json_file, dependencies_path):
    # Load JSON data
    with open(json_file, 'r') as f:
        data = json.load(f)

    results = defaultdict(list)  # To store the results by rule

    for item in data:
        jar = item['jar']
        url = item['url']
        rule = item.get('rule', "")
        license_url = item.get('license_url', "")

        jar_path = os.path.join(dependencies_path, jar)

        if os.path.exists(jar_path):
            license_source = extract_license(jar_path, jar, rule, license_url)
            results[rule].append((url, rule, license_source))
        else:
            print(f"Warning: {jar_path} does not exist.")

    # Print results
    for rule, entries in results.items():
        print("\n" + "="*72)
        print(f"Third party {rule} licenses")
        print("="*72)
        print(f"The following components are provided under the {rule} License. See project link for details.")
        print("The text of each license is also included in licenses/LICENSE-[project].txt.\n")
        for url, _, source in entries:
            # print(f"    {url} -> {rule} | {source}")
            print(f"    {url} -> {rule}")


if __name__ == "__main__":
    dependencies_path = "/Users/pengjunzhi/Code/hugegraph/install-dist/scripts/dependency/all_dependencies"
    os.makedirs('licenses', exist_ok=True)
    process_licenses('matched-licenses.json', dependencies_path)


# The code attempts to obtain licenses from the following sources:
#
# 1. **Predefined license files**:
#    - Checks the `licenses-predefined` directory for a matching license file.
#
# 2. **Inside the JAR file**:
#    - Extracts the JAR file and searches for files containing "license."
#
# 3. **License URL**:
#    - Uses the `license_url` to create a license file if none is found in the JAR or predefined directory and if the license rule isn't "Apache 2.0."
#
# 4. **Template license files**:
#    - Uses a template from the `licenses-tpl` directory based on the license rule if all else fails.
#
# These steps ensure that each project is provided with the appropriate license information and its source is documented.

