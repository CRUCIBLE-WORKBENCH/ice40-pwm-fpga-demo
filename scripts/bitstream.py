"""Compare all ASC configuration records, excluding comments and symbol labels."""
from pathlib import Path
import sys

def configuration(path):
    records={};header=None
    for line in Path(path).read_text().splitlines():
        line=line.strip()
        if not line:continue
        if line.startswith('.'):
            header=line
            if line.startswith(('.comment','.sym')):header=None
            else:
                assert header not in records,header
                records[header]=[]
        elif header is not None:records[header].append(line)
    assert '.device 1k' in records
    assert any(key.startswith('.logic_tile ') for key in records)
    # IceStorm allocates zero-initialized BRAM data for omitted ASC records.
    # iceunpack writes these defaults explicitly. Keep every actual data bit:
    # normalizing an omitted record never permits a nonzero decoded RAM word.
    for key in list(records):
        if key.startswith('.ramb_tile '):
            ram=key.replace('.ramb_tile ','.ram_data ',1)
            if ram not in records:records[ram]=['0'*64 for _ in range(16)]
    return records

if __name__=='__main__':
    left=configuration(sys.argv[1] if len(sys.argv)>1 else 'build/fpga.asc')
    right=configuration(sys.argv[2] if len(sys.argv)>2 else 'build/unpacked.asc')
    assert left==right,'PWM_CONFIGURATION_MISMATCH after bitstream decoding'
    print('PWM_DECODED_CONFIGURATION_MATCH records='+str(len(left)))
