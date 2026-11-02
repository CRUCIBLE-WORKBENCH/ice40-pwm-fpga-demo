"""Capture the exact inputs to one real stage before it executes."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
STAGES={
 'identity':['evidence/board.json'],
 'rtl':['rtl/pwm_demo.v','rtl/fpga_top.v','tests/tb_core.v','tests/tb_top.v'],
 'synth':['rtl/pwm_demo.v','rtl/fpga_top.v','scripts/synthesis.ys','scripts/models.py'],
 'mapped':['build/mapped.v','build/cells_sim.v','tests/tb_top.v'],
 'route':['build/fpga.json','constraints/icestick.pcf'],
 'pack':['build/fpga.asc','scripts/bitstream.py'],
 'negative':['tests/pwm_broken.v','tests/tb_core.v','build/fpga.json','build/fpga.asc','constraints/icestick.pcf','scripts/mutate_configuration.py','scripts/bitstream.py'],
}
mode=sys.argv[1]
files=STAGES[mode]+['crucible.lock','scripts/run.sh','scripts/provenance.py']
record={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files}
(ROOT/f'reports/{mode}_inputs.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8',newline='\n')
