# iCEstick PWM demonstration

**Status: software verification passes; physical deployment is incomplete. No board or programmer was available.** The original goal includes programming a physical FPGA and observing its behavior. A simulated design and a generated bitstream do not satisfy that requirement. **Crucible is beta.**

This candidate iCEstick design cycles through 0%, 25%, 50%, 75% and 100% PWM duty on red LED D1. Independent RTL and actual mapped-netlist simulation cover the full production sequence. Managed Yosys, nextpnr and IceStorm produce a routed, timing-checked, packed configuration. Behavioral, impossible-timing and configuration-bit controls test the verification guards.

Read the [ten-page software-verification PDF](docs/FPGA_PWM_iCEstick_Software_Verification_Ignytion_A4.pdf) or [editable A4 PowerPoint](docs/FPGA_PWM_iCEstick_Software_Verification_Ignytion_A4.pptx). [Compact results](evidence/summary.json), [candidate board references](evidence/board.json), [official model identity](evidence/models.json) and [document hashes](evidence/documents.sha256.json) are included. Fresh runs regenerate local `build/` and `reports/`; those directories stay outside Git.

## Recorded software results

Measured locally on 1 November 2026:

| Check | Observed result |
|---|---|
| Production RTL and mapped top | 5,243,400 cycles and 5,263,881 comparisons each |
| PWM coverage | All five duty stages, exact endpoint samples, 20,481 whole periods and sequence wrap |
| Core boundary/reset tests | Two parameter configurations; 10,120 cycles and 10,155 comparisons each |
| Final route resources | 47/1,280 logic cells, two I/O, two global buffers; no RAM or PLL |
| Final timing estimate | 191.35 MHz maximum frequency against the 12 MHz target |
| Bitstream | 32,220 bytes; 265 decoded configuration records agree; repacked bytes identical |
| Negative controls | Broken zero-duty endpoint, 1 GHz target and changed configuration bit rejected |
| Physical programming/observations | **Not performed; board/programmer unavailable** |

The frequency is the final nextpnr device-model estimate, not a measured board clock or vendor signoff result. The mapped simulation uses unchanged official iCE40 cell models and zero delays. Decoded configuration matching establishes serialization consistency; post-route logical equivalence and physical behavior remain unverified.

## Target, timing and reset contract

Candidate board: **Lattice iCEstick Evaluation Kit, iCE40HX1K, TQ144**. This is the software build target; it does not imply that the user owns or has purchased a board. The [manufacturer guide](https://www.latticesemi.com/view_document?document_id=50701) describes the nominal 12 MHz oscillator and D1 LED. Its LED table maps D1 to pin 99, and its known-issue note says pin 21 must remain an input. The [official nextpnr example PCF](https://github.com/YosysHQ/nextpnr/blob/main/ice40/examples/blinky/blinky.pcf) independently maps clock to 21 and LED1 to 99. The LED schematic shows active-high drive through a resistor to ground.

| Item | Contract |
|---|---|
| Top ports | `clk` input on pin 21; `led` output on pin 99 |
| PWM period | 256 clock samples |
| Duty sequence | Exactly 0, 64, 128, 192 and 256 high samples per period, then repeat |
| Stage hold | 4,096 PWM periods in the production top |
| Stage transition | Only when the phase wraps to zero |
| Startup | A configuration-initialized counter holds engine reset for seven clock edges |
| Engine reset | State reset is synchronous active high; LED is forced low while reset is asserted |

At a nominal 12 MHz clock, arithmetic predicts a 46.875 kHz carrier, 87.381333 ms per stage and 436.906667 ms per five-stage sequence. These are derived expectations, not measurements. There is no external reset pin. The output is a combinational PWM comparison; physical pulse integrity and transients require measurement. The top has one internal clock domain and an asynchronous LED observation output with no external receiving-clock constraint.

`pwm_demo` supports positive `STEP_PERIODS` values used here: 1, 2 and 4,096. The short core tests exercise the first two. Both full top simulations retain the real 4,096-period production configuration. They do not replace the counter with a faster implementation.

## 1. Prerequisites and correct shell

Use Linux x86-64/WSL, Bash, Python 3, Git and an existing Crucible beta installation. Run all Bash commands from this repository root, where `crucible.toml`, `crucible.lock`, `rtl/`, `tests/`, `constraints/` and `scripts/` reside. PowerShell commands are labelled separately. No PDK, separate pip environment or board is required for the software stages. Native runtime dependencies must be available for the managed artifacts on the host.

The lock pins Yosys 0.63.0, Icarus Verilog 14.0.0, nextpnr 0.10.0 and IceStorm 2026.04.03. The observed executables report Yosys 0.63+188 and nextpnr-0.10-22-gd6b4d3ed; the IceStorm package identity is recorded through the lock/checksum. Acquisition may download these archives on a new machine. Native Windows/macOS/ARM acquisition and an independent clean-machine reproduction have not been demonstrated.

## 2. Restore and inspect the managed environment

Linux/WSL Bash:

```bash
igny init
unset CRUCIBLE_ENV
igny --version
igny workspace sync
igny status
igny env show fpga-demo
igny tool show yosys --env fpga-demo
igny tool show iverilog --env fpga-demo
igny tool show nextpnr --env fpga-demo
igny tool show icepack --env fpga-demo
igny tool show iceunpack --env fpga-demo
python3 --version
bash scripts/run.sh identity
cat reports/tool_versions.txt
```

`igny init` initializes the outer workbench shell. `unset` removes an inherited environment override. `workspace sync` acquires missing locked tools and restores the named environment; it does not build this design or provide USB hardware access. `icepack` and `iceunpack` belong to `icestorm`. The catalogued binary `nextpnr` resolves to the iCE40 executable in this package; do not substitute an uncatalogued `nextpnr-ice40` command.

Stop on an acquisition, runtime or binding error and inspect the diagnostic. Version output alone does not verify the design. The existing workspace marker and lock are supplied: do not create another workspace over them. Every flow invocation selects `fpga-demo` explicitly. Some tools return nonzero for help/usage requests; that is not a design result.

## 3. Run every software stage in order

Linux/WSL Bash, after step 2:

```bash
bash scripts/run.sh rtl
bash scripts/run.sh synth
bash scripts/run.sh mapped
bash scripts/run.sh route
bash scripts/run.sh pack
bash scripts/run.sh negative
python3 scripts/verify.py
```

| Stage | Actual work | Principal output / expected result |
|---|---|---|
| `identity` | Record managed versions and actual Yosys resolution | `reports/tool_versions.txt`; `PWM_MANAGED_TOOLS_RECORDED` |
| `rtl` | Run both short core configurations and the complete production top | `reports/core_1.log`, `core_2.log`, `top_rtl.log`; positive markers below |
| `synth` | Map the real production RTL, check the result, copy/hash unchanged official cells | `build/fpga.json`, `build/mapped.v`, `build/cells_sim.v`; `PWM_REAL_ICE40_SYNTHESIS_COMPLETED` |
| `mapped` | Run the same full top observer against the actual mapped netlist | `reports/top_mapped.log`; identical comparison and stage totals |
| `route` | HX1K/TQ144 placement/routing, exact PCF, seed 1, 12 MHz clock | `build/fpga.asc`, `reports/route.json`; `PWM_REAL_ICE40_PLACEMENT_ROUTING_COMPLETED` |
| `pack` | Pack, unpack, compare configuration records and repack | `build/fpga.bin`, `unpacked.asc`, `repacked.bin`; `PWM_BITSTREAM_UNPACK_REPACK_BYTES_IDENTICAL` |
| `negative` | Run broken duty fixture, impossible timing target and actual one-bit packed/decoded mutation | Negative logs/exit files; `PWM_BEHAVIORAL_TIMING_AND_CONFIGURATION_CONTROLS_REJECTED` |
| `verify.py` | Check actual results, causal controls, tool/config/source identities and explicit open hardware state | `reports/summary.json`; verification and incomplete-deployment markers below |

The stages depend on earlier outputs: `synth` needs recorded identity, `mapped` needs synthesis/models, `route` needs synthesis, `pack` needs the route, and `negative` needs the positive route. The final observer requires every stage. Each stage records current input hashes and its process exit status. Changing a source, test, runner, model or constraint invalidates the affected evidence; rerun the affected stage and all dependent stages.

The full top tests simulate more than five million clock cycles each. Allow them to finish; they do not print a PASS until the full production sequence and wrap have been checked. The testbench's time scale is a functional simulation scale and does not replace the physical 12 MHz route constraint.

## 4. Inspect the actual results

Linux/WSL Bash:

```bash
cat reports/core_1.log
cat reports/core_2.log
cat reports/top_rtl.log
cat reports/top_mapped.log
tail -n 25 reports/synthesis.log
cat reports/models.json
cat reports/route.json
tail -n 25 reports/route.log
python3 scripts/bitstream.py
sha256sum build/fpga.bin build/repacked.bin
cat reports/broken.log
cat reports/broken_exit.txt
tail -n 20 reports/impossible.log
cat reports/impossible_exit.txt
cat reports/configuration_negative.log
cat reports/configuration_negative_exit.txt
cat reports/summary.json
```

Both core tests must print `PWM_CORE_PASS cycles=10120 checks=10155 full_periods=35`. Both full top runs must print:

```text
PWM_TOP_PASS cycles=5243400 checks=5263881 full_periods=20481
```

Their per-stage counts must be 4,097 complete periods at zero duty and 4,096 at each other duty. The extra zero-duty period is checked after the sequence wraps. The observer computes expected output from elapsed cycles without reading DUT internal phase, stage, duty or counter state.

The bitstream comparator requires `PWM_DECODED_CONFIGURATION_MATCH records=265`. It compares every logic/I/O/extra-bit record. Comments and symbol labels are excluded. [IceStorm's source](https://github.com/YosysHQ/icestorm/blob/main/icepack/icepack.cc) shows zero-initialized omitted RAM data; the comparator expands those defaults and retains all actual RAM bits. Repacked bytes must be identical. This does not establish post-route functional equivalence or physical loading.

The broken fixture must fail at cycle 256, phase zero, duty zero, observed one and expected zero. The impossible target must report a final frequency `FAIL at 1000.00 MHz`. The packed/decoded one-bit mutation must produce `PWM_CONFIGURATION_MISMATCH`. All three negative processes must exit one. Their outer `negative` runner returns success only after checking those expected failures; a compile error or missing tool is not a successful control.

The final observer prints both:

```text
PWM_SOFTWARE_SIMULATION_SYNTHESIS_ROUTE_TIMING_BITSTREAM_AND_CONTROLS_VERIFIED
PHYSICAL_DEPLOYMENT_INCOMPLETE_NO_BOARD_OR_PROGRAMMER
```

The second marker preserves the unfinished physical requirement. Do not interpret a software PASS as a deployed-board PASS. Raw tool logs may contain local runtime paths and are intentionally ignored by Git.

## 5. Troubleshooting

| Symptom | Check and next action |
|---|---|
| No workspace/environment or missing binary | Check the root, `igny status`, locked bindings and the `tool show` commands; restore with `igny workspace sync` |
| `nextpnr-ice40` is unavailable | Use the catalogued `igny run --env fpga-demo nextpnr` route in the runner |
| Official model file missing | Run `identity` then `synth`; the helper resolves the pinned Yosys artifact and requires one unchanged model file |
| Mapped simulation has unknown/unresolved cells | Inspect `reports/top_mapped_compile.log`; retain official cells and the supplied simulator flags |
| Observer reports stale inputs | Rebuild the affected stage and dependents against current files; do not reuse an older success log |
| ASC text differs after unpacking | Comments/symbols and explicit zero RAM defaults are normalized; any other configuration mismatch is a failure |
| Impossible timing control passes | Inspect the actual 1,000 MHz target and final nextpnr error; do not enable timing-failure overrides |
| No physical result | Hardware is absent; software work cannot remove the deployment requirement |

## 6. Open the reviewed whitepaper and inspect Git

Windows PowerShell, from this repository root:

```powershell
Invoke-Item .\docs\FPGA_PWM_iCEstick_Software_Verification_Ignytion_A4.pdf
Invoke-Item .\docs\FPGA_PWM_iCEstick_Software_Verification_Ignytion_A4.pptx
python scripts\preflight_git.py
```

The preflight uses Python's standard library. It checks public candidate paths, links, whitespace, executable index modes, document hashes and selected credential/personal-path patterns. It does not run EDA tools or program hardware. The PDF is searchable; the PPTX is its exact reviewed editable source.

Linux/WSL Bash, after reviewing the allowlisted content:

```bash
git status --short
git diff --check
git add -- .
git diff --cached --check
python3 scripts/preflight_git.py
git diff --cached --stat
git diff --cached
git branch --show-current
```

Require `GIT_PREFLIGHT_PASS`. The new candidate uses `demo/software-verified`; its README and whitepaper explicitly retain the open physical requirement. The runner must have index mode `100755`. If a Windows-created index needs that mode set:

```bash
git update-index --chmod=+x scripts/run.sh
python3 scripts/preflight_git.py
```

Do not force-add raw builds, bitstreams, logs, runtime payloads, personal configuration or agent/work notes. The compact evidence records the positive bitstream hash; regenerate it from the pinned source flow. No project-wide licence grant is invented; dependencies retain their own terms.

These are **manual commit/publication commands**, not commands already executed by this demonstration. Review the staged material and choose your author identity and public destination first:

```bash
git config user.name
git config user.email
git commit -m "Add software-verified iCEstick PWM demo with open hardware gate"
git remote -v
PUBLIC_REPOSITORY_URL='REPLACE_WITH_YOUR_PUBLIC_REPOSITORY_URL'
git remote add origin "$PUBLIC_REPOSITORY_URL"
git push -u origin HEAD
```

Replace the placeholder. Use `remote add` only if no `origin` exists; otherwise inspect `git remote get-url origin`. No script commits, changes remotes, pushes or publishes the project.

## 7. Future physical deployment: conditional manual steps

**Do not run this section without an actual confirmed iCEstick board and deliberate authorization to replace its SPI flash image. None of these hardware steps was executed.** Confirm board model/revision, HX1K/TQ144, pin mapping, supply/USB connection and host driver/permissions first. WSL USB pass-through is not configured or proven by this repository. Use the reviewed positive image, never a mutation or impossible-target scratch file.

After rerunning software verification, compare `build/fpga.bin` with the bitstream SHA-256 in `reports/summary.json` and the reviewed snapshot. A changed image requires a fresh review. The candidate iCEstick's onboard FTDI path is described in the manufacturer guide. The following explicit manual command uses IceStorm's default SPI flash programming flow and overwrites the current flash image:

```bash
sha256sum build/fpga.bin
igny tool show iceprog --env fpga-demo
igny run --env fpga-demo iceprog build/fpga.bin
```

Record the actual board identity, exact image hash, programmer/tool identity, command, exit status and programming log. Then measure the clock and LED waveform across all five duty levels and the sequence wrap, and capture startup/configuration behavior over repeated power cycles. Record measured period/high time, not only a visual impression of brightness. Review physical failures and update evidence and whitepaper before marking deployment complete. No automated programming mode is provided.

## Source layout and limits

`rtl/` contains the PWM engine and startup wrapper. `tests/` contains independent cycle/whole-period observers and the deliberate inclusive-comparator bug. `constraints/` fixes the two actual package pins. `scripts/` contains the managed build runner, source provenance, official model selection, configuration comparison and final observer. `evidence/` retains the reviewed snapshot; fresh runs write local `reports/`.

This demonstration does not establish physical deployment, observed clock/duty/startup/reset behavior, SDF simulation, post-route equivalence, other board/device/platform/tool configurations, environmental corners, vendor STA/signoff, ASIC layout or fabricated-silicon behavior. The original full project remains incomplete until physical acceptance is recorded.
