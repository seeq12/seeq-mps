import sys
import os
import json
import zipfile
import pathlib
import shutil
import argparse
import subprocess
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument(
    '-d', '--distribute',
    help='Upload the built files to their distribution channels.',
    action='store_true'
)
parser.add_argument(
    '-c', '--compile',
    help='Produce a compiled version of the code in addition to the source version',
    action='store_true'
)
parser.add_argument(
    '-a', '--addon',
    help='Produce a zipped version for installation through the addon manager.',
    action='store_true'
)
args = parser.parse_args()

# build the distribution
distribution_relative_dir = 'dist'
distribution_abs_dir = os.path.join(os.getcwd(), distribution_relative_dir)
if os.path.isdir(distribution_abs_dir):
    shutil.rmtree(distribution_abs_dir)

# Ensure 'build' package is installed
try:
    import build
except ImportError:
    print("Installing build module...")
    subprocess.run([sys.executable, "-m", "pip", "install", "build"])

# Build the wheel
builder = build.ProjectBuilder('.')
import tempfile

builder = build.ProjectBuilder('.')
with tempfile.TemporaryDirectory() as temp_dir:
    wheel_path = builder.build('wheel', temp_dir)
    shutil.move(wheel_path, os.path.join(distribution_abs_dir, os.path.basename(wheel_path)))

# Get the newest wheel file
wheel_files = list(Path(distribution_abs_dir).glob("*.whl"))
if not wheel_files:
    raise FileNotFoundError("No wheel file found in dist/")
source_wheel = max(wheel_files, key=os.path.getctime)
source_wheel_name = source_wheel.name
version = source_wheel_name.split('-')[1]

compiled_wheel = None
if args.compile:
    import compileall
    print('Compiling .py files to .pyc...')
    compiled_dir = os.path.join(distribution_abs_dir, 'compiled')
    os.makedirs(compiled_dir, exist_ok=True)

    # Compile all source files into .pyc under `compiled_dir`
    compileall.compile_dir(
        dir=os.getcwd(),
        force=True,
        quiet=1,
        legacy=True,
        ddir=os.getcwd(),
        optimize=2,
        rx=None
    )

    # Copy only .pyc files from __pycache__ into the compiled dir
    for root, dirs, files in os.walk(os.getcwd()):
        for file in files:
            if file.endswith('.pyc'):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, os.getcwd())
                dest_path = os.path.join(compiled_dir, rel_path)
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                shutil.copy2(full_path, dest_path)

    compiled_wheel = compiled_dir
    print(f'Compiled .pyc files placed in: {compiled_wheel}')

addon_manager_artifacts = []
if args.addon:
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
