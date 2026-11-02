#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
unset CRUCIBLE_ENV
mkdir -p build reports
mode="${1:-rtl}"
case "$mode" in identity|rtl|synth|mapped|route|pack|negative) ;; *) exit 2;; esac
trap 'echo "$?" >"reports/${mode}_exit.txt"' EXIT
python3 scripts/provenance.py "$mode"
case "$mode" in
  identity)
    cp evidence/board.json reports/board.json
    igny run --env fpga-demo yosys -V >reports/tool_versions.txt 2>&1
    igny run --env fpga-demo nextpnr --version >>reports/tool_versions.txt 2>&1
    igny run --env fpga-demo iverilog -V >>reports/tool_versions.txt 2>&1
    igny tool show yosys --env fpga-demo --json >reports/yosys_tool.json
    echo PWM_MANAGED_TOOLS_RECORDED
    ;;
  rtl)
    for periods in 1 2;do
      igny run --env fpga-demo iverilog -g2012 -s tb -Ptb.STEP_PERIODS="$periods" -o "build/core_$periods.vvp" tests/tb_core.v rtl/pwm_demo.v >"reports/core_${periods}_compile.log" 2>&1
      igny run --env fpga-demo vvp "build/core_$periods.vvp" >"reports/core_$periods.log" 2>&1
    done
    igny run --env fpga-demo iverilog -g2012 -s tb -o build/top_rtl.vvp tests/tb_top.v rtl/pwm_demo.v rtl/fpga_top.v >reports/top_rtl_compile.log 2>&1
    igny run --env fpga-demo vvp build/top_rtl.vvp >reports/top_rtl.log 2>&1
    cat reports/core_1.log reports/core_2.log reports/top_rtl.log
    ;;
  synth)
    igny run --env fpga-demo yosys -s scripts/synthesis.ys >reports/synthesis.log 2>&1
    python3 scripts/models.py
    echo PWM_REAL_ICE40_SYNTHESIS_COMPLETED
    ;;
  mapped)
    igny run --env fpga-demo iverilog -g2012 -DNO_ICE40_DEFAULT_ASSIGNMENTS -s tb -o build/top_mapped.vvp tests/tb_top.v build/mapped.v build/cells_sim.v >reports/top_mapped_compile.log 2>&1
    igny run --env fpga-demo vvp build/top_mapped.vvp >reports/top_mapped.log 2>&1
    cat reports/top_mapped.log
    ;;
  route)
    igny run --env fpga-demo nextpnr --hx1k --package tq144 --json build/fpga.json --pcf constraints/icestick.pcf --freq 12 --seed 1 --asc build/fpga.asc --report reports/route.json >reports/route.log 2>&1
    echo PWM_REAL_ICE40_PLACEMENT_ROUTING_COMPLETED
    ;;
  pack)
    igny run --env fpga-demo icepack build/fpga.asc build/fpga.bin >reports/pack.log 2>&1
    igny run --env fpga-demo iceunpack build/fpga.bin build/unpacked.asc >reports/unpack.log 2>&1
    igny run --env fpga-demo icepack build/unpacked.asc build/repacked.bin >reports/repack.log 2>&1
    cmp build/fpga.bin build/repacked.bin
    python3 scripts/bitstream.py
    echo PWM_BITSTREAM_UNPACK_REPACK_BYTES_IDENTICAL
    ;;
  negative)
    igny run --env fpga-demo iverilog -g2012 -s tb -o build/broken.vvp tests/tb_core.v tests/pwm_broken.v >reports/broken_compile.log 2>&1
    python3 scripts/mutate_configuration.py
    igny run --env fpga-demo icepack build/mutant.asc build/mutant.bin >reports/mutant_pack.log 2>&1
    igny run --env fpga-demo iceunpack build/mutant.bin build/mutant_decoded.asc >reports/mutant_unpack.log 2>&1
    set +e
    python3 scripts/bitstream.py build/fpga.asc build/mutant_decoded.asc >reports/configuration_negative.log 2>&1
    configuration_code=$?
    igny run --env fpga-demo vvp build/broken.vvp >reports/broken.log 2>&1
    sim_code=$?
    igny run --env fpga-demo nextpnr --hx1k --package tq144 --json build/fpga.json --pcf constraints/icestick.pcf --freq 1000 --seed 1 --asc build/impossible.asc --report reports/impossible.json >reports/impossible.log 2>&1
    timing_code=$?
    set -e
    echo "$sim_code" >reports/broken_exit.txt
    echo "$timing_code" >reports/impossible_exit.txt
    echo "$configuration_code" >reports/configuration_negative_exit.txt
    test "$sim_code" -ne 0
    test "$timing_code" -ne 0
    test "$configuration_code" -ne 0
    grep -q 'PWM_MISMATCH.*duty=0 got=1 expected=0' reports/broken.log
    grep -q 'FAIL' reports/impossible.log
    grep -q 'PWM_CONFIGURATION_MISMATCH' reports/configuration_negative.log
    echo PWM_BEHAVIORAL_TIMING_AND_CONFIGURATION_CONTROLS_REJECTED
    ;;
  *) echo 'Usage: bash scripts/run.sh identity|rtl|synth|mapped|route|pack|negative' >&2;exit 2;;
esac
