import sys
import os
import json
import zipfile
import pathlib
import shutil
import argparse
import subprocess

# build the distribution
distribution_relative_dir = 'dist'
distribution_abs_dir = os.path.join(os.getcwd(), distribution_relative_dir)
if os.path.isdir(distribution_abs_dir):
    shutil.rmtree(distribution_abs_dir)
build_command = [
    sys.executable, '-m', 'build',
    '--wheel',
    '--outdir', distribution_relative_dir]
subprocess.run(build_command, check=True)
source_wheel = max(
    [os.path.join(distribution_abs_dir, f) for f in os.listdir(distribution_abs_dir)],
    key=os.path.getctime
)

source_wheel_name = os.path.split(source_wheel)[-1]
version = source_wheel_name.split('-')[1]

addon_manager_artifacts = []
name = 'mps'
print(f'Creating {name}.addon')
# Ensure output folder exists
bin = os.path.join(os.getcwd(), 'bin')
if not os.path.exists(bin):
    os.makedirs(bin)

with open('addon.json') as json_file:
    parsed_json = json.load(json_file)
parsed_json['version'] = version

addon = os.path.join(bin, f'{name}.addon')
addon_meta = os.path.join(bin, f'{name}.addonmeta')

# Build addon
with zipfile.ZipFile(addon, 'w') as z:
    z.write(source_wheel, arcname=os.path.join('data-lab-functions', source_wheel_name))
    z.writestr('data-lab-functions/requirements.txt', f"./{source_wheel_name}")
    with z.open("addon.json", "w") as c:
        c.write(json.dumps(parsed_json, indent=2).encode("utf-8"))
    directory = pathlib.Path("./seeq/addons/mps/deployment_notebook/")
    for file in directory.rglob('*ipynb'):
        z.write(file, arcname=os.path.join('data-lab-functions', file.name))
    directory = pathlib.Path("./additional_content/")
    for file in directory.iterdir():
        z.write(file)
    addon_manager_artifacts.append(addon)
# Build addonmeta
print(f'Creating {name}.addonmeta')
with zipfile.ZipFile(addon_meta, 'w') as z:
    with z.open("addon.json", "w") as c:
        c.write(json.dumps(parsed_json, indent=2).encode("utf-8"))
    directory = pathlib.Path("./additional_content/")
    for file in directory.iterdir():
        z.write(file)
    addon_manager_artifacts.append(addon_meta)

print('Successfully created.')