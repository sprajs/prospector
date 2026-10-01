#!/usr/bin/env python3
"""Prepare the public-only Sites checkout and build, inside ignored Prospector storage."""
import shutil
import subprocess
from validate_register import ROOT


def prepare():
    source = ROOT / 'site'
    destination = ROOT / '.work/site-hosting'
    destination.mkdir(parents=True, exist_ok=True)
    for name in ['index.template.html', 'data.json', 'abstract.mjs', 'build.mjs', 'dev.mjs', 'logo.svg', 'abstract.test.mjs']:
        shutil.copyfile(source / name, destination / name)
    (destination / '.openai').mkdir(exist_ok=True)
    shutil.copyfile(source / '.openai/hosting.json', destination / '.openai/hosting.json')
    (destination / '.gitignore').write_text('node_modules/\n.sites-runtime/\n')
    subprocess.run(['node', 'build.mjs'], cwd=destination, check=True)
    print(destination.relative_to(ROOT))


if __name__ == '__main__':
    prepare()
