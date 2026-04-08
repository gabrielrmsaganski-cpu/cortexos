# Demo Mode

## Goal

Demo mode loads a coherent fictional dataset that produces:

- dashboard metrics
- timeline activity
- conflicts
- supersessions
- procedural memories
- explainable retrieval cases

## Dataset

Source file:

- `/home/saganski/workspace/experiments/cortexos/examples/demo-memories.json`

Themes included:

- launch date supersession
- support hub conflict
- office move timeline
- model strategy notes
- runtime procedure memory

## Commands

Seed only:

```bash
cd /home/saganski/workspace/experiments/cortexos
./.venv/bin/python scripts/seed_demo.py
```

Seed plus rebuild UI:

```bash
cd /home/saganski/workspace/experiments/cortexos
scripts/demo_mode.sh
```

UI-triggered seed:

- open dashboard
- click `Seed demo mode`

## Notes

- rerunning demo seed is safe
- duplicates in the same `wing/room` are skipped
- existing user data is not deleted
