#!/bin/bash
# Auto-chain remaining deterministic RRI slices through DW (A-mode, sequential — shared GPUs).
# rda is re-run first (v1 rejected by upper-review for a fail-open). ONE SLICE_DONE line per slice to stdout.
cd /home/takasan/egl
# guard: ensure the prior standalone rda process is fully gone before touching GPUs
until ! pgrep -f run_rri_rda_trial.py >/dev/null 2>&1; do sleep 5; done
sleep 4
echo "CHAIN_START (running rda rdec needval transform axis rqgate)"
for name in rda rdec needval transform axis rqgate; do
  rm -f experiments/rri_${name}_slice.json
  python3 experiments/run_rri_dw_slice.py $name >> experiments/rri_chain_${name}.log 2>&1
  python3 -c "
import json,os
p='experiments/rri_${name}_slice.json'
if os.path.exists(p):
    d=json.load(open(p)); print('SLICE_DONE ${name} completed=%s state=%s swaps=%s failures=%s avg=%ss'%(d.get('completed'),d.get('final_state'),d.get('swap_count'),d.get('swap_failures'),d.get('avg_swap_s')))
else:
    print('SLICE_DONE ${name} completed=ERROR no-json (see rri_chain_${name}.log)')
"
done
echo "CHAIN_DONE all 6 slices"
