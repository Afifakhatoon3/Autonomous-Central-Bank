# Autonomous Central Bank

## What This Is

An autonomous monetary policy engine built on GenLayer. It reads real-world data, proposes policy changes, and executes them through AI consensus - without any human vote.

**This is a policy engine, not a stablecoin issuer.**

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

# Quick Start

### Install GenLayer CLI

```bash
npm install -g genlayer
```

# Set network

```bash
genlayer network set studionet
```

# Deploy

```bash
genlayer deploy --contract contracts/acb.py
```

# Run tests

```bash
pip install -r requirements.txt
pytest tests/direct/ -v
```

# Contract API

## Lifecycle

- observe() - Start the contract

- pause() - Admin halt (stores state)

- unpause() - Resume (restores previous state)

## Observation

- fetch_data(sources) - Fetch and summarize URLs

## Proposal

- propose_policy(observation_id, direction, bond) - Create proposal

- cancel_proposal(proposal_id) - Cancel before evaluation

## Consensus

- evaluate_policy(proposal_id) - Trigger AI consensus

- execute_policy(proposal_id) - Write accepted policy

- finalize_failed(proposal_id) - Clean up failed proposal

## Views

- get_global_state() - Current lifecycle state

- get_active_policy() - Live policy

- get_proposal(proposal_id) - Full proposal record

- get_proposal_count() - Total proposals

- get_history(offset, limit) - Paginated history

- get_observation(observation_id) - Specific observation

- get_latest_observation() - Most recent observation

- get_bounds() - Safety bounds

- get_bond(address) - Bond balance for an address

# Direction Format

```
set_interest_rate:<value>       # 0 to 20 (percent)
set_collateral_ratio:<value>    # 100 to 200 (percent)
set_supply_adjustment:<value>   # -5 to +5 (percent)
```

Values are in milli-percent. 2.5 means 2.5%.

# Evaluation Logic

The contract classifies economic signals and matches them against the proposed direction:

- HAWKISH signal (inflation rising, rate hikes) + TIGHTENING proposal = ACCEPTED

- DOVISH signal (inflation falling, recession risk) + EASING proposal = ACCEPTED

- HAWKISH + EASING = REJECTED

- DOVISH + TIGHTENING = REJECTED

- NEUTRAL signal = INCONCLUSIVE

# Documentation

- docs/01-positioning.md - Problem and solution

- docs/02-state-machine.md - States and transitions

- docs/03-contract-methods.md - Full API reference

- docs/04-data-flow.md - How data moves

- docs/05-demo-scenarios.md - Demo walkthrough

- docs/06-weaknesses-and-fixes.md - Honest audit

# Verified Transactions

## All transactions verified on GenLayer Studionet Explorer.

## Action Result Transaction

- Deploy contract SUCCESS: https://explorer-studio.genlayer.com/tx/0x4f06756b0bcf1dddabe1856ff5455e4b0b38c279f3dcd47979d84680c79d9677

- observe() SUCCESS: https://explorer-studio.genlayer.com/tx/0x7037a5f0709f3f132e70c1866341119b876540098728dac742683ffcd414438b

- fetch_data() #1 SUCCESS: https://explorer-studio.genlayer.com/tx/0xda6c077ead17be479d6541ccd28b2e88ebbe89a016bb12339bf75e01b9ac8c82

- propose_policy() #1 (TIGHTENING) SUCCESS: https://explorer-studio.genlayer.com/tx/0xa5367f45b00db54bea1530e83874087fd128d1fc4e851243a0f18294bea72c7d

- evaluate_policy() #1 ACCEPTED: https://explorer-studio.genlayer.com/tx/0x3d2b22bb2ffbe165c715b39d9a60945be2809075bfde640bd1801710b41e9251

- execute_policy() #1 SUCCESS: https://explorer-studio.genlayer.com/tx/0x3d2b22bb2ffbe165c715b39d9a60945be2809075bfde640bd1801710b41e9251

- fetch_data() #2 SUCCESS: https://explorer-studio.genlayer.com/tx/0x94641338ef2238473760b15fb4c5a8ac04021f4b1287237cbcef1c3d8ce0febd

- propose_policy() #2 (EASING) SUCCESS: https://explorer-studio.genlayer.com/tx/0x40f2b0c0f4ce5847d956a07f72c39d304441c3f06f596dd31ea6a454b68dcc32

- evaluate_policy() #2 REJECTED: https://explorer-studio.genlayer.com/tx/0xcfd05017296a3b2cd47043b4d6caeaf5a089aaeba76c0ed1f9354b590504711c

- finalize_failed() #2 SUCCESS: https://explorer-studio.genlayer.com/tx/0x65f47f10e24e44bb3470e9aa2a2d94d967766fa3f071fefbc7537bf57e19571b

- pause() SUCCESS: https://explorer-studio.genlayer.com/tx/0x4c0b82e31e1a010a582b5f8c7522c2fa066761547c649189c953bf5a99cc5c50

- unpause() SUCCESS: https://explorer-studio.genlayer.com/tx/0x0416cf72c1f440debbcd811eeb56a962d4b21ff66f84b81bafc38f4c8838f7e4

# Limitations

- No real money movement (simulated bond only)
- Studionet only (no mainnet)
- No upgrade path (MVP)
- Some news sites block automated fetching (Reuters, Bloomberg)

See docs/06-weaknesses-and-fixes.md for the full audit.

# License

MIT