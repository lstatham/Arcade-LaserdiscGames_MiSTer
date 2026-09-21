#!/usr/bin/env python3
"""Merge core_jpeg's two same-clock dual-port-RAM write/read always blocks into
one so Quartus infers a true-dual-port RAM instead of erroring on multiple
drivers. Every affected RAM ties clk0_i and clk1_i to clk_i, so it is
behaviour-preserving. Idempotent. Usage: patch_core_jpeg.py <dir-of-core_jpeg>"""
import re, sys, pathlib
BLOCK = re.compile(
    r'always @ \(posedge clk0_i\)\s*\n\s*begin\s*\n'
    r'(?P<wr0>\s*if \(wr0_i\)\s*\n\s*ram\[addr0_i\][^\n;]* <= data0_i[^\n;]*;)\s*\n'
    r'\s*\n?(?P<rd0>\s*ram_read0_q <= ram\[addr0_i\];)\s*\n\s*end\s*\n'
    r'\s*\n\s*always @ \(posedge clk1_i\)\s*\n\s*begin\s*\n'
    r'(?P<wr1>\s*if \(wr1_i\)\s*\n\s*ram\[addr1_i\][^\n;]* <= data1_i[^\n;]*;)\s*\n'
    r'\s*\n?(?P<rd1>\s*ram_read1_q <= ram\[addr1_i\];)\s*\n\s*end',
    re.DOTALL)
def merge(m):
    return ("always @ (posedge clk0_i)\nbegin  // MERGED for Quartus TDP RAM (both ports use clk_i)\n"
            + m.group('wr0') + "\n\n" + m.group('wr1') + "\n\n"
            + m.group('rd0') + "\n" + m.group('rd1') + "\nend")
root = pathlib.Path(sys.argv[1])
patched = 0
for p in sorted(root.rglob("*.v")):
    txt = p.read_text()
    if "posedge clk1_i" not in txt:
        continue
    new, n = BLOCK.subn(merge, txt)
    if n >= 1:
        p.write_text(new); patched += 1; print(f"patched {p.name} ({n} block)")
    elif "MERGED for Quartus" in txt:
        print(f"already patched {p.name}")
    else:
        print(f"WARNING: {p.name} has clk1_i but no matching block", file=sys.stderr)
print(f"done: {patched} file(s) patched")
