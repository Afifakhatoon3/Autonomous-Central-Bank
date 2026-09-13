# Data Flow

## Overview

This document describes how data moves through the Autonomous Central
Bank (ACB) — from the internet, through the contract, to the final
policy decision. Every arrow is verifiable on-chain or via GenLayer's
consensus layer.

## High-Level Flow

Internet (news, data)
        │
        ▼
[ Intelligent Oracle ]   ← GenLayer fetches URLs
        │
        ▼
[ Observation Object ]   ← LLM summarizes the data
        │
        ▼
[ Policy Proposal ]      ← Anyone proposes a direction
        │
        ▼
[ Consensus Evaluation ] ← Validators judge independently
        │
        ▼
[ Policy Decision ]      ← ACCEPTED / REJECTED / INCONCLUSIVE
        │
        ▼
[ Live Policy ]          ← If ACCEPTED, written to state
        │
        ▼
[ Consumers ]            ← Stablecoins, DAOs, agents read the policy

## Step 1: Data Ingestion

Trigger: `fetch_data(sources)`

Inputs:
- `sources`: list of HTTPS URLs (news, economic data, feeds)

Process:
1. Caller invokes `fetch_data()`.
2. GenLayer's Intelligent Oracle fetches each URL.
3. If any source fails to fetch, the entire call reverts.
   No partial observations are stored.
4. For each successful source, the raw content is passed to an LLM.
5. LLM produces a summary of the source.
6. All summaries are combined into one Observation object.
7. Observation is stored in `observations[]` with a timestamp.
8. `latest_observation` is updated.

Output:
- Observation object with:
  - observation_id
  - source_urls
  - fetched_at
  - summary

Trust assumptions:
- Sources are HTTPS only. No localhost, IP literals, or .local.
- Validators agree on semantically equivalent summaries, not
  byte-identical ones. GenLayer's Equivalence Principle handles this.
- Source authenticity is not verified. The contract trusts the URL
  because the caller chose it and the proposal bond makes spam costly.

## Step 2: Policy Proposal

Trigger: `propose_policy(observation_id, direction, bond)`

Inputs:
- `observation_id`: which observation to base the policy on
- `direction`: what the policy should do
- `bond`: locked stake to prevent spam

Direction Format:
- Must follow a structured format: `<parameter>:<value>`
- Direction sets the new absolute value, not a delta.
- Allowed parameters and their value ranges:
  - `set_interest_rate` — value between 0 and 20 (percent)
  - `set_collateral_ratio` — value between 100 and 200 (percent)
  - `set_supply_adjustment` — value between -5 and +5 (percent)
- Value must be a signed decimal within the safety bounds.
- The contract parses the string. Invalid formats are rejected with
  INVALID_DIRECTION error.
- Example: `set_interest_rate:2.5` sets the interest rate to 2.5%.

Process:
1. Caller invokes `propose_policy()`.
2. Contract verifies:
   - Global state is OBSERVING
   - Cooldown has elapsed
   - Observation exists and is fresh
   - Direction is well-formed and inside safety bounds
   - Bond meets minimum
3. Bond is locked in the simulated ledger.
4. Proposal is appended to `proposals[]` with state PROPOSED.
5. Global state changes to POLICY_PROPOSED.

Output:
- Proposal object with:
  - proposal_id
  - proposer
  - observation_id
  - direction
  - bond
  - created_at
  - state (PROPOSED)

## Step 3: Consensus Evaluation

Trigger: `evaluate_policy(proposal_id)`

Inputs:
- The stored observation (summary + source URLs)
- The proposed direction
- The safety bounds

Process:
1. Caller invokes `evaluate_policy()`.
2. Global state → CONSENSUS_PENDING.
3. Per-policy state → EVALUATING.
4. Contract calls `gl.nondet.exec_prompt()` with a structured prompt:
   - "Given this observation: [summary]"
   - "And this proposed policy: [direction]"
   - "Is this policy appropriate? Answer ACCEPTED, REJECTED, or
     INCONCLUSIVE, with a short rationale."
5. GenLayer validators each run the prompt independently.
6. Validators compare results using GenLayer's standard validators
   protocol. A verdict is accepted if it satisfies GenLayer's
   equivalence criteria. Otherwise the verdict is INCONCLUSIVE.
7. Verdict is stored with the proposal.

Note: All state transitions inside evaluate_policy are atomic. If the
call reverts at any point, no state change occurs. The contract does
not get stuck in CONSENSUS_PENDING.

Output:
- Proposal updated with:
  - verdict (ACCEPTED / REJECTED / INCONCLUSIVE)
  - rationale (LLM-generated text)
  - evaluated_at

## Step 4: Policy Execution

Trigger: `execute_policy(proposal_id)` (only if verdict is ACCEPTED)

Process:
1. Caller invokes `execute_policy()`.
2. Contract verifies:
   - Global state is CONSENSUS_REACHED
   - Proposal state is ACCEPTED
   - Not already executed
3. Policy is written to `active_policy`:
   - direction
   - based_on_observation
   - executed_at
   - generation (auto-incrementing)
4. Per-policy state → EXECUTED.
5. Global state → POLICY_EXECUTED → OBSERVING (same call).
6. Bond is refunded to proposer.

Output:
- Active policy updated
- History appended

## Step 5: Consumer Read

Trigger: Any external contract or user calls a view method.

Process:
1. Consumer calls `get_active_policy()`.
2. Returns current live policy with metadata.
3. Consumer can also call `get_history()` to see all past policies
   and their rationales.

Output:
- Policy object that consumers act on.

Note: Consumers act on the policy by their own rules. ACB does not
force any contract to follow the policy.

## Data Types

### Observation

| Field | Type | Description |
|---|---|---|
| observation_id | int | Auto-incrementing ID |
| source_urls | list[str] | HTTPS URLs that were fetched |
| fetched_at | int | Unix timestamp |
| summary | str | LLM-generated combined summary |

### Proposal

| Field | Type | Description |
|---|---|---|
| proposal_id | int | Auto-incrementing ID |
| proposer | str | Address that proposed |
| observation_id | int | Reference to observation |
| direction | str | Policy direction |
| bond | int | Locked bond amount |
| created_at | int | Unix timestamp |
| state | str | PROPOSED / EVALUATING / ACCEPTED / REJECTED / INCONCLUSIVE / EXECUTED |
| verdict | str | Final verdict |
| rationale | str | LLM-generated reasoning |

### Active Policy

| Field | Type | Description |
|---|---|---|
| direction | str | Current policy |
| based_on_observation | int | Observation ID |
| executed_at | int | Unix timestamp |
| generation | int | Auto-incrementing counter |

## Data Integrity

| Property | How it is preserved |
|---|---|
| Observation is immutable | Once stored, observations are never modified |
| Proposal history is append-only | Proposals are never deleted |
| Policy is versioned | Each execution increments generation |
| Rationale is preserved | Every verdict stores its LLM reasoning |
| Bond is accounted | Every bond is either refunded or slashed |

## Failure Modes and Recovery

| Failure | Behavior |
|---|---|
| Source URL unreachable | fetch_data reverts entirely, no partial observation |
| LLM summary is garbage | Validators reject via consensus |
| Consensus cannot agree | Verdict is INCONCLUSIVE, bond refunded |
| Bond too low | propose_policy reverts |
| Stale observation | propose_policy reverts |
| Malformed direction | propose_policy reverts with INVALID_DIRECTION |
| evaluate_policy reverts mid-call | Atomic rollback, no state change |
| Admin pauses | No new proposals, evaluation can still complete |

## What Data Does NOT Flow

- No user private data
- No wallet keys
- No transaction history of any user
- No token balances
- No external API credentials

The ACB only reads public internet data and writes public policy decisions. Nothing else.