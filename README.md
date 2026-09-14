# Autonomous Central Bank

## What This Is

An autonomous monetary policy engine built on GenLayer. It reads real-world data, proposes policy changes, and executes them through AI consensus - without any human vote.

**This is a policy engine, not a stablecoin issuer.**

## Track

GenLayer Agent Tank — Autonomous Protocols

## Live Deployment

- Network: GenLayer Studionet
- Contract address: `0x6bB1737270A9feBb70A0Bcd05a82D0C9b213A4bf`
- Deployed: Sep 14, 2026

### Verified On-Chain

All lifecycle paths tested on Studionet:

- `observe()` → INIT to OBSERVING
- `fetch_data()` → clean LLM summary, no reasoning tags
- `propose_policy()` → policy proposed, bond locked
- `evaluate_policy()` → GenLayer consensus verdict
- **ACCEPTED case**: HAWKISH observation + TIGHTENING proposal
- **REJECTED case**: HAWKISH observation + EASING proposal
- `execute_policy()` → policy live, generation incremented
- `finalize_failed()` → bond slashed on REJECTED
- `pause()` / `unpause()` → admin halt with state restore

## How It Works

1. **Observe** - Anyone calls `observe()` to start the contract
2. **Fetch data** - Anyone calls `fetch_data()` with HTTPS URLs
3. **Propose** - Anyone calls `propose_policy()` with a direction
4. **Evaluate** - Validators reach consensus on the verdict
5. **Execute** - If accepted, the policy goes live

## Quick Start

### Install GenLayer CLI

```bash
npm install -g genlayer
```

## Set network

```bash
genlayer network set studionet
```

## Deploy

```bash
genlayer deploy --contract contracts/acb.py
```

## Run tests

```bash
pip install -r requirements.txt
pytest tests/direct/ -v
```

## Contract API

## Lifecycle

· observe() - Start the contract
· pause() - Admin halt (stores state)
· unpause() - Resume (restores previous state)

## Observation

· fetch_data(sources) - Fetch and summarize URLs

Proposal

· propose_policy(observation_id, direction, bond) - Create proposal
· cancel_proposal(proposal_id) - Cancel before evaluation

Consensus

· evaluate_policy(proposal_id) - Trigger AI consensus
· execute_policy(proposal_id) - Write accepted policy
· finalize_failed(proposal_id) - Clean up failed proposal

Views

· get_global_state() - Current lifecycle state
· get_active_policy() - Live policy
· get_proposal(proposal_id) - Full proposal record
· get_proposal_count() - Total proposals
· get_history(offset, limit) - Paginated history
· get_observation(observation_id) - Specific observation
· get_latest_observation() - Most recent observation
· get_bounds() - Safety bounds
· get_bond(address) — Bond balance for an address

## Direction Format

```
set_interest_rate:<value>       # 0 to 20 (percent)
set_collateral_ratio:<value>    # 100 to 200 (percent)
set_supply_adjustment:<value>   # -5 to +5 (percent)
```

Values are in milli-percent. 2.5 means 2.5%.

## Evaluation Logic

The contract classifies economic signals and matches them against the proposed direction:

· HAWKISH signal (inflation rising, rate hikes) + TIGHTENING proposal = ACCEPTED
· DOVISH signal (inflation falling, recession risk) + EASING proposal = ACCEPTED
· HAWKISH + EASING = REJECTED
· DOVISH + TIGHTENING = REJECTED
· NEUTRAL signal = INCONCLUSIVE

## Documentation

· docs/01-positioning.md - Problem and solution
· docs/02-state-machine.md - States and transitions
· docs/03-contract-methods.md - Full API reference
· docs/04-data-flow.md - How data moves
· docs/05-demo-scenarios.md - Demo walkthrough
· docs/06-weaknesses-and-fixes.md - Honest audit

## Verified Transactions

All transactions verified on GenLayer Studionet Explorer.

# Action Result Transaction
1 Deploy contract SUCCESS 0x4f0675...d9677
2 observe() SUCCESS 0x7037a5...4438b
3 fetch_data() #1 SUCCESS 0xda6c07...c8c82
4 propose_policy() #1 (TIGHTENING) SUCCESS 0xa5367f...a72c7d
5 evaluate_policy() #1 ACCEPTED 0x3d2b22...41e9251
6 execute_policy() #1 SUCCESS 0x7e1499...8a9ee
7 fetch_data() #2 SUCCESS 0x946413...ce0febd
8 propose_policy() #2 (EASING) SUCCESS 0x40f2b0...68dcc32
9 evaluate_policy() #2 REJECTED 0xcfd050...04711c
10 finalize_failed() #2 SUCCESS 0x65f47f...571b
11 pause() SUCCESS 0x4c0b82...cc5c50
12 unpause() SUCCESS 0x0416cf...38f7e4

## Limitations

· No real money movement (simulated bond only)
· Studionet only (no mainnet)
· No upgrade path (MVP)
· Some news sites block automated fetching (Reuters, Bloomberg)

See docs/06-weaknesses-and-fixes.md for the full audit.

## License

MIT

```