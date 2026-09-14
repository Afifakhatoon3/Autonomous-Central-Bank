#!/usr/bin/env bash
#
# Demo walkthrough for Autonomous Central Bank.
#
# Preconditions:
#   - genlayer CLI installed
#   - network set to studionet
#   - contract deployed (address below)
#
# Usage:
#   bash scripts/demo.sh
#
# Note: This script uses the GenLayer CLI. Commands may vary slightly
# based on CLI version. Refer to README.md for the canonical walkthrough.

set -e

CONTRACT="0x6bB1737270A9feBb70A0Bcd05a82D0C9b213A4bf"
NEWS_URL="https://en.wikipedia.org/wiki/2021%E2%80%932023_inflation_surge"

echo "=== Autonomous Central Bank Demo ==="
echo "Contract: $CONTRACT"
echo ""

echo "[1/9] Reading initial state..."
genlayer call "$CONTRACT" get_global_state
echo ""

echo "[2/9] Calling observe()..."
genlayer write "$CONTRACT" observe
sleep 2
genlayer call "$CONTRACT" get_global_state
echo ""

echo "[3/9] Fetching real-world data..."
genlayer write "$CONTRACT" fetch_data "[\"$NEWS_URL\"]"
echo "Waiting 60s for LLM summary..."
sleep 60
genlayer call "$CONTRACT" get_latest_observation
echo ""

echo "[4/9] Proposing a TIGHTENING policy..."
genlayer write "$CONTRACT" propose_policy 1 "set_interest_rate:2.5" 100
sleep 2
genlayer call "$CONTRACT" get_global_state
echo ""

echo "[5/9] Evaluating proposal (expect ACCEPTED)..."
genlayer write "$CONTRACT" evaluate_policy 1
echo "Waiting 60s for consensus..."
sleep 60
genlayer call "$CONTRACT" get_proposal 1
echo ""

echo "[6/9] Executing accepted policy..."
genlayer write "$CONTRACT" execute_policy 1
sleep 2
genlayer call "$CONTRACT" get_active_policy
echo ""

echo "[7/9] Waiting for cooldown..."
sleep 12
genlayer write "$CONTRACT" fetch_data "[\"$NEWS_URL\"]"
sleep 60
genlayer call "$CONTRACT" get_latest_observation
echo ""

echo "[8/9] Proposing an EASING policy (expect REJECTED)..."
genlayer write "$CONTRACT" propose_policy 2 "set_supply_adjustment:5" 100
sleep 2
genlayer write "$CONTRACT" evaluate_policy 2
sleep 60
genlayer call "$CONTRACT" get_proposal 2
genlayer write "$CONTRACT" finalize_failed 2
echo ""

echo "[9/9] Testing pause/unpause..."
genlayer write "$CONTRACT" pause
genlayer call "$CONTRACT" get_global_state
genlayer write "$CONTRACT" unpause
genlayer call "$CONTRACT" get_global_state
echo ""

echo "=== Demo complete ==="