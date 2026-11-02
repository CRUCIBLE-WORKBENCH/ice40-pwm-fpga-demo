"""Copy the actual pinned Yosys simulation library without changing cell models."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
info=json.loads((ROOT/'reports/yosys_tool.json').read_text())
resolved=info['resolved']
assert resolved['env']=='fpga-demo' and resolved['runnable']
install=next(item for item in info['installed'] if item['version']==resolved['version'])
candidates=list(Path(install['install_path']).glob('**/ice40/cells_sim.v'))
assert len(candidates)==1,candidates
data=candidates[0].read_bytes()
(ROOT/'build/cells_sim.v').write_bytes(data)
record={'provider':'yosys','version':resolved['version'],'file':'ice40/cells_sim.v','sha256':hashlib.sha256(data).hexdigest(),'modification':'none'}
(ROOT/'reports/models.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8',newline='\n')
print('PWM_OFFICIAL_ICE40_CELL_MODELS_COPIED_UNCHANGED')
