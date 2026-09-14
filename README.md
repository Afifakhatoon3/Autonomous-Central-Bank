# Autonomous Central Bank

An autonomous monetary policy engine built on GenLayer. It reads real-world data, proposes policy changes, and executes them through AI consensus - without any human vote.

**This is a policy engine, not a stablecoin issuer.**

## Live Deployment

- **Network:** GenLayer Studionet
- **Contract address:** `0x6bB1737270A9feBb70A0Bcd05a82D0C9b213A4bf`
- **Deployed:** Sep 14, 2026
- **Explorer:** [View contract](https://explorer-studio.genlayer.com/address/0x6bB1737270A9feBb70A0Bcd05a82D0C9b213A4bf)

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

### Set network

```bash
genlayer network set studionet
```

### Deploy

```bash
genlayer deploy --contract contracts/acb.py
```

### Run tests

```bash
pip install -r requirements.txt
pytest tests/direct/ -v
```

## Project Structure

```
autonomous-central-bank/
├── contracts/
│   └── acb.py                     # GenLayer Intelligent Contract
├── docs/
│   ├── 01-positioning.md          # Problem and solution
│   ├── 02-state-machine.md        # States and transitions
│   ├── 03-contract-methods.md     # Full API reference
│   ├── 04-data-flow.md            # How data moves through the system
│   ├── 05-demo-scenarios.md       # Demo walkthrough
│   └── 06-weaknesses-and-fixes.md # Honest audit of 27 weaknesses
├── deploy/
│   └── deployScript.ts            # Deploy reference
├── scripts/
│   └── demo.sh                    # End-to-end demo script
├── tests/
│   └── direct/
│       └── test_acb.py            # Direct tests for the contract
├── .gitignore
├── LICENSE                        # MIT
├── README.md                      # This file
├── gltest.config.yaml             # GenLayer test configuration
├── pyproject.toml                 # Python project metadata
└── requirements.txt               # Python dependencies
```

### Key files

- **`contracts/acb.py`** - The entire contract. Single file, ~550 lines. Contains storage, lifecycle, observation, proposal, consensus, and view methods.
- **`docs/06-weaknesses-and-fixes.md`** - Start here if you want to understand the design tradeoffs. Every known weakness is named, fixed, or scoped.
- **`scripts/demo.sh`** - Reproduces the full on-chain walkthrough (observe → fetch → propose → evaluate → execute → pause).

## Contract API

### Lifecycle
- `observe()` - Start the contract
- `pause()` - Admin halt (stores state)
- `unpause()` - Resume (restores previous state)

### Observation
- `fetch_data(sources)` - Fetch and summarize URLs

### Proposal
- `propose_policy(observation_id, direction, bond)` - Create proposal
- `cancel_proposal(proposal_id)` - Cancel before evaluation

### Consensus
- `evaluate_policy(proposal_id)` - Trigger AI consensus
- `execute_policy(proposal_id)` - Write accepted policy
- `finalize_failed(proposal_id)` - Clean up failed proposal

### Views
- `get_global_state()` - Current lifecycle state
- `get_active_policy()` - Live policy
- `get_proposal(proposal_id)` - Full proposal record
- `get_proposal_count()` - Total proposals
- `get_history(offset, limit)` - Paginated history
- `get_observation(observation_id)` - Specific observation
- `get_latest_observation()` - Most recent observation
- `get_bounds()` - Safety bounds
- `get_bond(address)` — Bond balance for an address

## Direction Format

```
set_interest_rate:<value>       # 0 to 20 (percent)
set_collateral_ratio:<value>    # 100 to 200 (percent)
set_supply_adjustment:<value>   # -5 to +5 (percent)
```

Values are in milli-percent. `2.5` means 2.5%.

## Evaluation Logic

The contract classifies economic signals and matches them against the proposed direction:

- **HAWKISH** signal (inflation rising, rate hikes) + **TIGHTENING** proposal = ACCEPTED
- **DOVISH** signal (inflation falling, recession risk) + **EASING** proposal = ACCEPTED
- **HAWKISH** + **EASING** = REJECTED
- **DOVISH** + **TIGHTENING** = REJECTED
- **NEUTRAL** signal = INCONCLUSIVE

## Verified Transactions

All transactions verified on GenLayer Studionet Explorer.

| # | Action | Result | Transaction |
|---|--------|--------|-------------|
| 1 | Deploy contract | SUCCESS | [0x4f0675...](https://explorer-studio.genlayer.com/tx/0x4f06756b0bcf1dddabe1856ff5455e4b0b38c279f3dcd47979d84680c79d9677) |
| 2 | `observe()` | SUCCESS | [0x7037a5...](https://explorer-studio.genlayer.com/tx/0x7037a5f0709f3f132e70c1866341119b876540098728dac742683ffcd414438b) |
| 3 | `fetch_data()` #1 | SUCCESS | [0xda6c07...](https://explorer-studio.genlayer.com/tx/0xda6c077ead17be479d6541ccd28b2e88ebbe89a016bb12339bf75e01b9ac8c82) |
| 4 | `propose_policy()` #1 (TIGHTENING) | SUCCESS | [0xa5367f...](https://explorer-studio.genlayer.com/tx/0xa5367f45b00db54bea1530e83874087fd128d1fc4e851243a0f18294bea72c7d) |
| 5 | `evaluate_policy()` #1 | **ACCEPTED** | [0x3d2b22...](https://explorer-studio.genlayer.com/tx/0x3d2b22bb2ffbe165c715b39d9a60945be2809075bfde640bd1801710b41e9251) |
| 6 | `execute_policy()` #1 | SUCCESS | [0x7e1499...](https://explorer-studio.genlayer.com/tx/0x7e1499a9563494abb3f83bb9893892746a4ae57bb75b243a1cb2fe7b8e98a9ee) |
| 7 | `fetch_data()` #2 | SUCCESS | [0x946413...](https://explorer-studio.genlayer.com/tx/0x94641338ef2238473760b15fb4c5a8ac04021f4b1287237cbcef1c3d8ce0febd) |
| 8 | `propose_policy()` #2 (EASING) | SUCCESS | [0x40f2b0...](https://explorer-studio.genlayer.com/tx/0x40f2b0c0f4ce5847d956a07f72c39d304441c3f06f596dd31ea6a454b68dcc32) |
| 9 | `evaluate_policy()` #2 | **REJECTED** | [0xcfd050...](https://explorer-studio.genlayer.com/tx/0xcfd05017296a3b2cd47043b4d6caeaf5a089aaeba76c0ed1f9354b590504711c) |
| 10 | `finalize_failed()` #2 | SUCCESS | [0x65f47f...](https://explorer-studio.genlayer.com/tx/0x65f47f10e24e44bb3470e9aa2a2d94d967766fa3f071fefbc7537bf57e19571b) |
| 11 | `pause()` | SUCCESS | [0x4c0b82...](https://explorer-studio.genlayer.com/tx/0x4c0b82e31e1a010a582b5f8c7522c2fa066761547c649189c953bf5a99cc5c50) |
| 12 | `unpause()` | SUCCESS | [0x0416cf...](https://explorer-studio.genlayer.com/tx/0x0416cf72c1f440debbcd811eeb56a962d4b21ff66f84b81bafc38f4c8838f7e4) |

## Documentation

- [01 — Positioning](docs/01-positioning.md)
- [02 — State Machine](docs/02-state-machine.md)
- [03 — Contract Methods](docs/03-contract-methods.md)
- [04 — Data Flow](docs/04-data-flow.md)
- [05 — Demo Scenarios](docs/05-demo-scenarios.md)
- [06 — Weaknesses and Fixes](docs/06-weaknesses-and-fixes.md)

## Limitations

- No real money movement (simulated bond only)
- Studionet only (no mainnet deployment)
- No upgrade path (MVP scope)
- Some news sites block automated fetching (Reuters, Bloomberg)

See [docs/06-weaknesses-and-fixes.md](docs/06-weaknesses-and-fixes.md)
for the complete audit of 27 known weaknesses.

## License

MIT — see [LICENSE](LICENSE)