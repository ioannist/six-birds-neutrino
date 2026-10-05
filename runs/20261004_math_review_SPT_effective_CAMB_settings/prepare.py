"""Freeze configuration-style controls and weighted saved-row coordinates."""
from copy import deepcopy
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import subprocess
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
names = ['omegabh2', 'omegach2', 'H0', 'logA', 'ns', 'tau', 'mnu']
sources = []
def source(path):
    sources.append({'path': str(path.relative_to(ROOT)),
                    'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    return path

old_dirs = {'A': '20260212_060311_662922_cobaya_spt2018_desi_lcdm_mnu',
            'B': '20260212_072014_910159_cobaya_sptd1_desi_lcdm_mnu'}
new_dirs = {'A': '20261003_math_review_chain_A_seed301',
            'B': '20261003_math_review_chain_B_seed305'}
snapshot_dirs = {'A': '20261004_math_review_spt_chain_snapshots_fourteenth_A',
                 'B': '20261004_math_review_spt_chain_snapshots_fifteenth_B'}
records, versions = {}, {}
for target in ['A', 'B']:
    old_dir, new_dir = ROOT/'runs'/old_dirs[target], ROOT/'runs'/new_dirs[target]
    old_cfg = yaml.safe_load(source(old_dir/'resolved.yaml').read_text())
    new_cfg = yaml.safe_load(source(new_dir/'resolved.yaml').read_text())
    assert old_cfg['likelihood'] == new_cfg['likelihood']
    assert set(old_cfg['params']) == set(new_cfg['params'])
    for name in old_cfg['params']:
        for key in ['prior', 'value', 'drop']:
            assert old_cfg['params'][name].get(key) == new_cfg['params'][name].get(key)
    old_extra, new_extra = old_cfg['theory']['camb']['extra_args'], new_cfg['theory']['camb']['extra_args']
    assert 'lmax' not in old_extra and new_extra['lmax'] == 4095
    assert {k: v for k, v in new_extra.items() if k != 'lmax'} == old_extra
    updated, = (old_dir/'chains').glob('*.updated.yaml')
    old_updated = yaml.safe_load(source(updated).read_text())
    versions[target] = {'archived_CAMB': old_updated['theory']['camb']['version'],
                        'archived_Cobaya': old_updated['version']}
    for style, cfg in [('original_style', old_cfg), ('restoration_style', new_cfg)]:
        folder = HERE/target/style
        folder.mkdir(parents=True)
        # Only model definitions are passed to get_model; no output or sampler is run.
        cfg = {k: deepcopy(cfg[k]) for k in ['theory', 'likelihood', 'params']}
        cfg['packages_path'] = str(ROOT/'external/cobaya_packages')
        cfg['debug'] = False
        (folder/'input.yaml').write_text(yaml.safe_dump(cfg, sort_keys=False))
    original_chain, = (old_dir/'chains').glob('*.1.txt')
    snapshot = json.loads(source(ROOT/'runs'/snapshot_dirs[target]/'snapshot_receipt.json').read_text())
    frozen_chain = ROOT/snapshot['files'][0]['snapshot']
    points, choices = {}, {}
    for label, path in [('original', original_chain), ('restoration', frozen_chain)]:
        raw = source(path).read_bytes()
        lines = raw.decode().splitlines()
        header = next(line for line in lines if line.startswith('#')).lstrip('#').split()
        assert len(header) == len(set(header)) and set(names) <= set(header)
        rows = [line.split() for line in lines if line.strip() and not line.startswith('#')]
        first = len(rows)//5
        weights = [Fraction(row[0]) for row in rows[first:]]
        assert all(w > 0 and w.denominator == 1 for w in weights)
        ordered = sorted(range(first, len(rows)), key=lambda i: Fraction(rows[i][header.index('mnu')]))
        for q in [Fraction(1, 2), Fraction(95, 100)]:
            threshold, cumulative = q*sum(weights), Fraction(0)
            for i in ordered:
                cumulative += Fraction(rows[i][0])
                if cumulative >= threshold:
                    break
            key = label + ('_median' if q == Fraction(1, 2) else '_p95')
            points[key] = {n: float(rows[i][header.index(n)]) for n in names}
            choices[key] = {'source_chain': str(path.relative_to(ROOT)), 'stored_row_index': i,
                            'burnin_stored_rows': first, 'mass_quantile': str(q),
                            'holding_time': int(Fraction(rows[i][0])),
                            'mass': points[key]['mnu'],
                            'posterior_draw_claim': label == 'restoration'}
    points['restoration_median_mass_plus_001'] = dict(points['restoration_median'])
    points['restoration_median_mass_plus_001']['mnu'] += .01
    records[target] = {'point_selection': choices, 'points': points}
    (HERE/target/'points.json').write_text(json.dumps(points, indent=2, allow_nan=False)+'\n')

source(ROOT/'src/sbt_spt_audit/likelihoods/candl_cobaya.py')
source(ROOT/'src/sbt_spt_audit/likelihoods/desi_dr2_bao.py')
old_adapter = subprocess.run(['git', 'show', 'ffdaf4b:src/sbt_spt_audit/likelihoods/candl_cobaya.py'],
                             cwd=ROOT, check=True, capture_output=True).stdout
(HERE/'pre_review_adapter.py').write_bytes(old_adapter)
out = {'utc': datetime.now(timezone.utc).isoformat(), 'scope': 'current_stack_configuration_style_controls',
       'records': records, 'archived_versions': versions, 'sources': sources,
       'historical_stack_reconstructed': False, 'historical_numeric_target_identity_certified': False,
       'samplers_or_paper_modified': False}
with (HERE/'selection_receipt.json').open('x') as handle:
    handle.write(json.dumps(out, indent=2, allow_nan=False)+'\n')
print('Frozen five selected coordinates for each SPT target and both configuration styles.')
