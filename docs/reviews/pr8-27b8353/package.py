"""Copy only review artifacts into a separate publication branch and local ZIP."""
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

source = Path(__file__).resolve().parent
destination = Path('/tmp/docs-guardian-pr8-round3-publication/docs/reviews/pr8-27b8353')
destination.mkdir(parents=True, exist_ok=True)
files = sorted(p for p in source.iterdir()
               if p.is_file() and p.suffix in {'.txt', '.json', '.png', '.html', '.py', '.cjs'})
manifest = {
    'reviewed_commit': '27b835360c9e8dc530f842b780ee14ccf73e9f26',
    'files': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
}
(source / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
files = sorted(set(files + [source / 'manifest.json']))
for item in files:
    shutil.copy2(item, destination / item.name)
archive = Path('/tmp/docs-guardian-pr8-round3-evidence.zip')
with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as package:
    for item in files:
        package.write(item, item.name)
print(f'{len(files)} artifacts copied to {destination}')
print(f'ZIP: {archive} ({archive.stat().st_size} bytes)')
