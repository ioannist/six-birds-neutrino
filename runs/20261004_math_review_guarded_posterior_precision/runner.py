"""Require the pinned native module before executing the archived precision tool."""
import hashlib
import json
from pathlib import Path
import sys
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
receipt = json.loads((HERE/'selection_receipt.json').read_text())
import classy
import classy._classy as native
assert Path(native.__file__).resolve() == Path(receipt['native_module_path']).resolve()
assert hashlib.sha256(Path(native.__file__).read_bytes()).hexdigest() == receipt['native_module_sha256']
sys.path.insert(0,str(ROOT/'scripts'))
sys.path.insert(0,str(HERE))
from run_cobaya import _validate_classy_backend
configuration = yaml.safe_load(Path(sys.argv[sys.argv.index('--config')+1]).read_text())
assert _validate_classy_backend(configuration)['module_sha256'] == receipt['native_module_sha256']
from runner_snapshot import main
main(required_backend='classy')
