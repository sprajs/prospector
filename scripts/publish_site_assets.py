#!/usr/bin/env python3
"""Upload only generated public assets; verify exact S3 versions and anonymous CDN bytes."""
import argparse
import base64
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
CACHE = 'public, max-age=31536000, immutable'


def aws(profile, *args):
    result = subprocess.run(['aws', '--profile', profile, '--region', 'eu-west-2',
                             '--output', 'json', *args], capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stderr.strip())
    return json.loads(result.stdout) if result.stdout.strip() else {}


def delivery(url, expected, content_type):
    request = urllib.request.Request(url, headers={
        'Origin': 'https://prospector-cosmology.sprajs.chatgpt.site', 'Accept-Encoding': 'gzip'})
    with urllib.request.urlopen(request, timeout=30) as response:
        headers = response.headers
        encoded = response.read()
        body = gzip.decompress(encoded) if headers.get('Content-Encoding') == 'gzip' else encoded
        if body != expected:
            raise RuntimeError('Anonymous delivery byte mismatch: ' + url)
        if headers.get('Access-Control-Allow-Origin') != '*':
            raise RuntimeError('Missing public CORS: ' + url)
        if headers.get('Content-Type') != content_type or headers.get('Cache-Control') != CACHE:
            raise RuntimeError('Unexpected content type or caching: ' + url)
        return {k: headers.get(k) for k in ['Content-Type', 'Content-Encoding', 'Cache-Control',
                'Access-Control-Allow-Origin', 'X-Cache', 'ETag']} | {'encoded_bytes': len(encoded)}


def publish(profile):
    subprocess.run(['node', str(ROOT / 'site/build.mjs'), '--assets-only'], check=True)
    config = json.loads((ROOT / 'site/assets-config.json').read_text())
    manifest = json.loads((ROOT / 'site/.work/assets-manifest.json').read_text())
    identity = aws(profile, 'sts', 'get-caller-identity')['Arn']
    if ':assumed-role/prospector-assets-deployer/' not in identity:
        raise RuntimeError('Use the dedicated prospector-assets-deployer role')
    if set(manifest['assets']) != {'register', 'style', 'app', 'logo'}:
        raise RuntimeError('Unexpected public selection')
    records = {}
    scratch = ROOT / '.work/site-assets-verify'
    scratch.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=scratch) as temp:
        for name, asset in manifest['assets'].items():
            source = ROOT / 'site/.work/public-assets' / Path(asset['key']).name
            body = source.read_bytes()
            digest = hashlib.sha256(body).hexdigest()
            if digest != asset['sha256'] or asset['key'] != f"assets/{name}.{digest}.{source.suffix[1:]}":
                raise RuntimeError('Local identity mismatch')
            # Create-only PUT is atomic. A retry may reuse exactly the same existing bytes.
            try:
                head = aws(profile, 's3api', 'head-object', '--bucket', config['bucket'], '--key', asset['key'])
            except RuntimeError as error:
                if '(404)' not in str(error) and '(NotFound)' not in str(error):
                    raise
                try:
                    aws(profile, 's3api', 'put-object', '--bucket', config['bucket'], '--key', asset['key'],
                        '--body', str(source), '--if-none-match', '*', '--content-type', asset['content_type'],
                        '--cache-control', CACHE, '--checksum-sha256', base64.b64encode(bytes.fromhex(digest)).decode())
                except RuntimeError as collision:
                    if 'PreconditionFailed' not in str(collision):
                        raise
                head = aws(profile, 's3api', 'head-object', '--bucket', config['bucket'], '--key', asset['key'])
            if head.get('ContentType') != asset['content_type'] or head.get('CacheControl') != CACHE:
                raise RuntimeError('Existing object metadata mismatch')
            version = head['VersionId']
            restored = Path(temp) / name
            aws(profile, 's3api', 'get-object', '--bucket', config['bucket'], '--key', asset['key'],
                '--version-id', version, str(restored))
            if restored.read_bytes() != body:
                raise RuntimeError('Exact S3 version byte mismatch')
            url = config['origin'] + '/' + asset['key']
            records[name] = {'uri': f"s3://{config['bucket']}/{asset['key']}", 'version_id': version,
                             'sha256': digest, 'url': url, 'delivery': delivery(url, body, asset['content_type'])}
    release = {'schema': 'prospector-public-assets-release/v1', 'verified_utc': datetime.now(timezone.utc).isoformat(),
               'origin': config['origin'], 'manifest': manifest, 'objects': records,
               'deployment_identity': identity, 'repository_revision': subprocess.check_output(
                   ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
               'repository_dirty': bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT))}
    (ROOT / 'site/assets-release.json').write_text(json.dumps(release, indent=2) + '\n')
    print('Verified four exact S3 versions and anonymous CloudFront deliveries; site/assets-release.json')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', default='prospector-assets')
    publish(parser.parse_args().profile)
