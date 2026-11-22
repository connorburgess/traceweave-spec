"""Acquire only the two pinned public snapshots; execute no acquired code."""
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import tarfile
from datetime import datetime, timezone
from urllib.request import urlopen

REPOS = (
    ('go-spew', 'davecgh/go-spew', '8991bc29aa16c548c550c7ff78260e27b9ab7c73',
     '1b93a317849ee09d3d7e4f1d20c2b78ddb230b4becb12d7c224c927b9d470251'),
    ('hey', 'rakyll/hey', 'af177063f85bd935c55f1f2ee59c2898d9654f82',
     'd0bc204f82616d966e412365cc98afa1a8a9a15be07614e4770e84295e7e83ef'),
)
BASE = Path('.local/go-census')
records = []
for name, repo, commit, expected_license in REPOS:
    destination = BASE / 'sources' / name
    if destination.exists():
        raise SystemExit(f'refusing to overwrite {destination}')
    url = f'https://codeload.github.com/{repo}/tar.gz/{commit}'
    with urlopen(url, timeout=60) as response:
        archive = response.read()
    (BASE / 'archives').mkdir(parents=True, exist_ok=True)
    (BASE / 'archives' / f'{name}-{commit}.tar.gz').write_bytes(archive)
    skipped = []
    with tarfile.open(fileobj=io.BytesIO(archive), mode='r:gz') as source:
        for member in source:
            parts = PurePosixPath(member.name).parts
            if not parts or member.name.startswith('/') or '..' in parts:
                raise ValueError(f'unsafe archive member {member.name}')
            relative = PurePosixPath(*parts[1:])
            if str(relative) == '.':
                continue
            output = destination.joinpath(*relative.parts)
            if member.isdir():
                output.mkdir(parents=True, exist_ok=True)
            elif member.isfile():
                output.parent.mkdir(parents=True, exist_ok=True)
                with source.extractfile(member) as stream:
                    output.write_bytes(stream.read())
            else:
                skipped.append({'path': str(relative), 'type': repr(member.type)})
    license_sha = hashlib.sha256((destination / 'LICENSE').read_bytes()).hexdigest()
    if license_sha != expected_license:
        raise ValueError(f'license hash mismatch for {repo}')
    records.append({'repository': repo, 'commit': commit, 'url': url,
                    'acquiredUTC': datetime.now(timezone.utc).isoformat(),
                    'archiveSHA256': hashlib.sha256(archive).hexdigest(),
                    'licenseSHA256': license_sha, 'skippedSpecialMembers': skipped})
BASE.joinpath('acquisition.json').write_text(json.dumps(records, indent=2) + '\n')
print(json.dumps(records, indent=2))
