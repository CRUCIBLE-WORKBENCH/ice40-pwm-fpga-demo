"""Inspect actual RTL/mapped, route, packed configuration and causal controls."""
from pathlib import Path
from collections import Counter
import hashlib,json,re
from bitstream import configuration

ROOT=Path(__file__).resolve().parents[1];R=ROOT/'reports'
digest=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
inputs={}
for mode in ('identity','rtl','synth','mapped','route','pack','negative'):
    assert int((R/f'{mode}_exit.txt').read_text())==0,mode
    record=json.loads((R/f'{mode}_inputs.json').read_text())
    for p,expected in record.items():assert digest(p)==expected,mode+' stale input: '+p
    inputs[mode]=record
for number in (1,2):
    text=(R/f'core_{number}.log').read_text()
    assert 'PWM_CORE_PASS cycles=10120 checks=10155 full_periods=35' in text
    assert not re.search(r'(?i)fatal|mismatch|error',text)
top={}
for mode in ('rtl','mapped'):
    text=(R/f'top_{mode}.log').read_text()
    assert 'PWM_TOP_PASS cycles=5243400 checks=5263881 full_periods=20481' in text
    assert not re.search(r'(?i)fatal|mismatch|error',text)
    rows=[tuple(map(int,row)) for row in re.findall(r'PWM_TOP_STAGE stage=(\d+) duty=(\d+) full_periods=(\d+)',text)]
    assert rows==[(0,0,4097),(1,64,4096),(2,128,4096),(3,192,4096),(4,256,4096)]
    top[mode]={'cycles':5243400,'comparisons':5263881,'whole_periods':20481,'stage_periods':rows}
models=json.loads((R/'models.json').read_text())
assert models['provider']=='yosys' and models['modification']=='none'
assert models['sha256']==digest('build/cells_sim.v')
synth=json.loads((ROOT/'build/fpga.json').read_text())
ports=synth['modules']['fpga_top']['ports']
assert {name:value['direction'] for name,value in ports.items()}=={'clk':'input','led':'output'}
all_cells=synth['modules']['fpga_top']['cells'].values()
for cell in all_cells:
    if cell['type']=='$scopeinfo':assert not cell['connections']
cells=Counter(cell['type'] for cell in all_cells if cell['type']!='$scopeinfo')
assert cells['SB_LUT4']>0 and any(name.startswith('SB_DFF') for name in cells)
assert not any(name.startswith('$') for name in cells)
synthlog=(R/'synthesis.log').read_text()
assert 'Found and reported 0 problems.' in synthlog and 'ERROR:' not in synthlog
pcf=(ROOT/'constraints/icestick.pcf').read_text()
assert re.findall(r'^set_io (\w+) (\d+)$',pcf,re.M)==[('clk','21'),('led','99')]
runner=(ROOT/'scripts/run.sh').read_text()
assert '--hx1k --package tq144' in runner and '--freq 12 --seed 1' in runner
assert '--pcf-allow-unconstrained' not in runner and '--timing-allow-fail' not in runner
route=json.loads((R/'route.json').read_text())
assert len(route['fmax'])==1
timing=next(iter(route['fmax'].values()))
assert timing['constraint']==12 and timing['achieved']>=12
log=(R/'route.log').read_text()
assert 'PASS at 12.00 MHz' in log and 'Program finished normally.' in log
assert not re.search(r'ERROR:|unconstrained|no clock',log,re.I)
assert route['utilization']['ICESTORM_LC']['used']==47
assert route['utilization']['SB_IO']['used']==2
assert configuration(ROOT/'build/fpga.asc')==configuration(ROOT/'build/unpacked.asc')
data=(ROOT/'build/fpga.bin').read_bytes()
assert data==(ROOT/'build/repacked.bin').read_bytes() and len(data)>10000
assert data[:4]==bytes.fromhex('ff0000ff') or bytes.fromhex('7eaa997e') in data[:128]
assert configuration(ROOT/'build/fpga.asc')!=configuration(ROOT/'build/mutant_decoded.asc')
for label in ('broken','impossible','configuration_negative'):
    assert int((R/f'{label}_exit.txt').read_text())==1,label
negative=(R/'broken.log').read_text()
assert 'cycle=256 elapsed=256 phase=0 stage=0 duty=0 got=1 expected=0' in negative
assert '_PASS' not in negative
impossible=(R/'impossible.log').read_text()
assert re.search(r'ERROR: Max frequency .*FAIL at 1000\.00 MHz',impossible)
assert 'PWM_CONFIGURATION_MISMATCH after bitstream decoding' in (R/'configuration_negative.log').read_text()
versions=(R/'tool_versions.txt').read_text()
assert 'Yosys 0.63+' in versions and 'nextpnr-0.10-22-gd6b4d3ed' in versions
assert 'Icarus Verilog version 14.0' in versions
lock=json.loads((ROOT/'crucible.lock').read_text())
tools={tool['name']:tool['version'] for env in lock['environments'] for tool in env['tools']}
assert tools=={'yosys':'0.63.0','iverilog':'14.0.0','nextpnr':'0.10.0','icestorm':'2026.04.03'}
board=json.loads((R/'board.json').read_text())
assert board['clock_pin']==21 and board['led_pin']==99 and board['clock_hz']==12000000
assert not board['board_available'] and not board['programming_performed']
summary={'measurement_date':'2026-11-01','project_state':'SOFTWARE VERIFIED; PHYSICAL DEPLOYMENT INCOMPLETE',
 'target':{k:v for k,v in board.items() if k!='sources'},'tools':tools,
 'nextpnr_version':'0.10-22-gd6b4d3ed','simulation':top,'core_regressions':{'step_periods':[1,2],'cycles_each':10120,'comparisons_each':10155},
 'utilization':route['utilization'],'synthesized_cells':dict(cells),
 'timing':{'clock_constraint_mhz':12,'final_estimated_fmax_mhz':timing['achieved'],'scope':'nextpnr HX1K device model, final routed design; no measured clock or vendor signoff'},
 'pwm':{'samples_per_period':256,'high_samples':[0,64,128,192,256],'periods_per_stage':4096,'nominal_carrier_hz':12000000/256,'nominal_stage_seconds':1048576/12000000,'nominal_sequence_seconds':5242880/12000000},
 'bitstream':{'bytes':len(data),'sha256':digest('build/fpga.bin'),'configuration_records':len(configuration(ROOT/'build/fpga.asc')),'decode_compare':'all logic/IO/extra-bit records match; omitted RAM initialization expands to zero','repack':'byte identical'},
 'negative_controls':{'duty':'zero duty gains one sample in deliberately broken fixture; simulator exit 1','timing':'1000 MHz target rejected by final route analysis; nextpnr exit 1','configuration':'one logic configuration bit mutated, packed, decoded and rejected; observer exit 1'},
 'models':models,'sources':board['sources'],'inputs':inputs,
 'limits':'No physical board/programmer, programming, LED/clock/reset measurement, post-route functional equivalence, SDF simulation, vendor STA/signoff or silicon observation. Full deployment gate remains unmet.'}
(R/'summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8',newline='\n')
print('PWM_SOFTWARE_SIMULATION_SYNTHESIS_ROUTE_TIMING_BITSTREAM_AND_CONTROLS_VERIFIED')
print('PHYSICAL_DEPLOYMENT_INCOMPLETE_NO_BOARD_OR_PROGRAMMER')
