"""Create a local one-bit logic-configuration mutation for the decoder guard."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
lines=(ROOT/'build/fpga.asc').read_text().splitlines()
number=lines.index('.logic_tile 1 1')+1
assert set(lines[number])<=set('01')
lines[number]=('1' if lines[number][0]=='0' else '0')+lines[number][1:]
(ROOT/'build/mutant.asc').write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')
print('PWM_ONE_CONFIGURATION_BIT_MUTATED tile=1,1 row=0 column=0')
