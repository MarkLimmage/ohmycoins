#!/bin/bash
echo "Generating Demo Data for Audit Logs..."
docker compose exec backend python tests/populate_trade_audits.py
docker compose exec backend python tests/populate_kill_switch_history.py
echo "Done."
