"""Kenneth French data acquisition and validation."""
import io
import re
import pandas as pd


def parse_returns(text):
    lines = text.splitlines()
    start = next(i for i, line in enumerate(lines)
                 if 'Average Value Weighted Returns' in line and 'Daily' in line)
    header = next(i for i in range(start + 1, len(lines)) if 'HiTec' in lines[i] and 'Manuf' in lines[i])
    rows = []
    for line in lines[header + 1:]:
        if not re.match(r'^\s*\d{8},', line):
            if rows:
                break
            continue
        rows.append(line.strip())
    frame = pd.read_csv(io.StringIO(lines[header] + '\n' + '\n'.join(rows)), index_col=0)
    frame.index = pd.to_datetime(frame.index.astype(str), format='%Y%m%d')
    selected = frame[['HiTec', 'Manuf']].astype(float)
    import numpy as np
    if not np.isfinite(selected.values).all() or selected.isin([-99.99, -999]).any().any() or (selected <= -100).any().any():
        raise ValueError('invalid return or French missing sentinel')
    if selected.index.has_duplicates:
        raise ValueError('duplicate dates')
    if not selected.index.is_monotonic_increasing:
        raise ValueError('invalid chronological ordering')
    return selected / 100


def acquire(config, cache, offline=False, refresh=False):
    """Only accept pinned bytes; revision mismatch never silently replaces cache."""
    import hashlib
    import json
    import zipfile
    import urllib.request
    from datetime import datetime, UTC
    from pathlib import Path

    cache = Path(cache)
    cache.mkdir(parents=True, exist_ok=True)
    archive_path = cache / 'french.zip'
    provenance_path = cache / 'provenance.json'
    access_time = None
    if offline and not archive_path.exists():
        raise FileNotFoundError('Offline reproduction requires a validated local french.zip cache')
    if not offline and (refresh or not archive_path.exists()):
        try:
            with urllib.request.urlopen(config['url'], timeout=60) as response:
                downloaded = response.read()
            access_time = datetime.now(UTC).isoformat()
        except OSError:
            if not archive_path.exists():
                raise
        else:
            if hashlib.sha256(downloaded).hexdigest() != config['archive_sha256']:
                raise ValueError('Upstream revision/checksum changed: do not use revised bytes. Re-run --offline with the pinned local cache or review and deliberately repin config.')
            archive_path.write_bytes(downloaded)
    blob = archive_path.read_bytes()
    archive_hash = hashlib.sha256(blob).hexdigest()
    if archive_hash != config['archive_sha256']:
        raise ValueError('Cached archive checksum/revision mismatch')
    with zipfile.ZipFile(io.BytesIO(blob)) as archive:
        member = next(name for name in archive.namelist() if name.lower().endswith('.csv'))
        text = archive.read(member).decode('utf-8-sig')
    selected = parse_returns(text).loc[config['start']:config['end']]
    snapshot = selected.to_csv(index_label='date', float_format='%.8f', lineterminator='\n').encode()
    snapshot_hash = hashlib.sha256(snapshot).hexdigest()
    if snapshot_hash != config['snapshot_sha256']:
        raise ValueError('Selected snapshot checksum/revision mismatch')
    (cache / 'selected.csv').write_bytes(snapshot)
    prior = json.loads(provenance_path.read_text()) if provenance_path.exists() else {}
    provenance = dict(url=config['url'], accessed_utc=access_time or prior.get('accessed_utc'), archive_sha256=archive_hash, snapshot_sha256=snapshot_hash, member=member, source_header=text.splitlines()[0])
    provenance_path.write_text(json.dumps(provenance, indent=2) + '\n')
    return selected, provenance


def audit_returns(frame, split):
    """Observed coverage: absent weekdays include exchange holidays, not proven gaps."""
    import numpy as np
    extrema = {}
    for sector in frame.columns:
        values = frame[sector]
        extrema[sector] = dict(min=float(values.min()), min_date=values.idxmin().strftime('%Y-%m-%d'), max=float(values.max()), max_date=values.idxmax().strftime('%Y-%m-%d'), mean=float(values.mean()), std=float(values.std()))
    return dict(rows=len(frame), first_date=frame.index.min().strftime('%Y-%m-%d'), last_date=frame.index.max().strftime('%Y-%m-%d'), missing_values=int(frame.isna().sum().sum()), nonfinite_values=int((~np.isfinite(frame.values)).sum()), duplicate_dates=int(frame.index.duplicated().sum()), absent_weekdays_between_observed_endpoints=len(pd.bdate_range(frame.index.min(),frame.index.max()).difference(frame.index)), train_rows=int((frame.index < split).sum()), test_rows=int((frame.index >= split).sum()), rows_by_year={str(year):int(n) for year,n in frame.groupby(frame.index.year).size().items()}, sector_extrema=extrema)


def main():
    import argparse
    import json
    from pathlib import Path
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--offline', action='store_true')
    parser.add_argument('--refresh', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    frame, provenance = acquire(json.loads((root / 'config/study.json').read_text()), root / 'data', args.offline, args.refresh)
    print(json.dumps(dict(rows=len(frame), **provenance), indent=2))


if __name__ == '__main__':
    main()
