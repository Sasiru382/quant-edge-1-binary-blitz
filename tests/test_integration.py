import hashlib
import json
from pathlib import Path
import subprocess
import sys


def test_offline_cli_reproduces_pinned_real_data_numeric_outputs(tmp_path):
    root = Path(__file__).resolve().parents[1]
    config = json.loads((root/'config/study.json').read_text())
    config.update(bootstrap_replicates=9, simulation_size=2000, df_grid=[4,10])
    config_path = tmp_path/'config.json'
    config_path.write_text(json.dumps(config))
    target = tmp_path/'output'
    command = [sys.executable,'-m','src.study','--offline','--config',str(config_path),'--out',str(target)]
    subprocess.run(command,cwd=root,check=True,capture_output=True,text=True)
    results = json.loads((target/'results.json').read_text())
    assert results['audit']['rows'] == 5031
    assert results['provenance']['snapshot_sha256'] == config['snapshot_sha256']
    assert len(results['risk']) == 20
    from pypdf import PdfReader
    pdf = PdfReader(target/'study.pdf')
    assert len(pdf.pages) == 6
    text = '\n'.join(page.extract_text() for page in pdf.pages)
    assert 'Haar' in text
    assert 'ES is not validated' in text
    assert (target/'study.md').exists()
    assert len(list(target.glob('*.png'))) == 3
    first = {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in target.iterdir() if p.is_file()}
    subprocess.run(command,cwd=root,check=True,capture_output=True,text=True)
    second = {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in target.iterdir() if p.is_file()}
    assert first == second
