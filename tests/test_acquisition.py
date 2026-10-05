import hashlib
import io
import json
import zipfile
import pytest
from src import data
from tests.test_data import SAMPLE


def test_pinned_cache_offline_and_revision_failure(tmp_path):
    payload = io.BytesIO()
    with zipfile.ZipFile(payload, 'w') as archive:
        archive.writestr('sample.csv', SAMPLE)
    blob = payload.getvalue()
    snapshot = data.parse_returns(SAMPLE).to_csv(index_label='date', float_format='%.8f', lineterminator='\n').encode()
    config = dict(url='https://invalid.example/data.zip', archive_sha256=hashlib.sha256(blob).hexdigest(), snapshot_sha256=hashlib.sha256(snapshot).hexdigest(), start='2006-01-01', end='2025-12-31')
    (tmp_path / 'french.zip').write_bytes(blob)
    result, provenance = data.acquire(config, tmp_path, offline=True)
    assert len(result) == 2
    assert provenance['archive_sha256'] == config['archive_sha256']
    assert provenance['snapshot_sha256'] == config['snapshot_sha256']
    (tmp_path / 'french.zip').write_bytes(b'changed upstream')
    with pytest.raises(ValueError, match='revision|checksum'):
        data.acquire(config, tmp_path, offline=True)
    (tmp_path / 'french.zip').write_bytes(blob)
    revised = tmp_path / 'revised.zip'
    revised.write_bytes(b'new upstream revision')
    config['url'] = revised.as_uri()
    with pytest.raises(ValueError, match='Upstream revision/checksum changed'):
        data.acquire(config, tmp_path, refresh=True)
    assert (tmp_path / 'french.zip').read_bytes() == blob
    recovered, _ = data.acquire(config, tmp_path, offline=True)
    assert len(recovered) == 2
