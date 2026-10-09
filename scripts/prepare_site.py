#!/usr/bin/env python3
"""Prepare the public-only Sites checkout and build, inside ignored Prospector storage."""
import argparse
import shutil
import subprocess
from pathlib import Path
from validate_register import ROOT


def prepare(destination=None):
    source = ROOT / 'site'
    destination = (destination or ROOT / '.work/site-hosting').resolve()
    if not destination.is_relative_to((ROOT / '.work').resolve()):
        raise ValueError('The public checkout must stay inside Prospector .work')
    destination.mkdir(parents=True, exist_ok=True)
    for name in ['index.template.html', 'data.json', 'abstract.mjs', 'build.mjs', 'dev.mjs', 'logo.svg', 'abstract.test.mjs', 'assets.mjs', 'assets-config.json', 'assets-release.json']:
        shutil.copyfile(source / name, destination / name)
    (destination / '.openai').mkdir(exist_ok=True)
    shutil.copyfile(source / '.openai/hosting.json', destination / '.openai/hosting.json')
    (destination / '.gitignore').write_text('node_modules/\n.sites-runtime/\n.work/\n')
    subprocess.run(['node', 'build.mjs'], cwd=destination, check=True)
    print(destination.relative_to(ROOT))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', type=Path)
    prepare(parser.parse_args().destination)
