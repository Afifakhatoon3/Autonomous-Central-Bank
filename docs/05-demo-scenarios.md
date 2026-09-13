# Demo Scenarios

## Overview

This document defines the exact scenarios that will be demonstrated
during the Agent Tank submission. Each scenario is end-to-end,
reproducible on Studionet, and shows a distinct capability of the
Autonomous Central Bank (ACB).

Four scenarios are planned: three core and one optional. Each takes
under 2 minutes to run.

Note: LLM-generated outputs (summaries, rationales, verdicts) are
illustrative in this document. Actual output will vary between runs.
GenLayer's equivalence principle ensures semantic agreement, not
byte-identical output.

Note: The cooldown between proposals is set to a short value (e.g.
10 seconds) for the demo deployment. In production, this would be
longer.

## Scenario 1: Happy Path — Data-Driven Policy Execution

Purpose: Show the full lifecycle from data to executed policy.

### Narrative

A news article reports rising inflation. A proposer reads this,
submits an observation, proposes a rate hike, validators approve it,
and the policy goes live.

### Steps

1. **Observe**
   - Caller invokes `observe()`
   - Global state: INIT → OBSERVING

2. **Fetch data**
   - Caller invokes `fetch_data(["https://www.reuters.com/markets/"])`
   - Observation stored with an LLM-generated summary of recent
     market news
   - Returns observation_id = 1

3. **Propose policy**
   - Caller invokes `propose_policy(1, "set_interest_rate:2.5", 100)`
   - Bond locked
   - Global state: OBSERVING → POLICY_PROPOSED

4. **Evaluate**
   - Caller invokes `evaluate_policy(1)`
   - Validators read observation + direction
   - Verdict: ACCEPTED
   - Rationale: LLM-generated reasoning (illustrative)
   - Global state: POLICY_PROPOSED → CONSENSUS_REACHED

5. **Execute**
   - Caller invokes `execute_policy(1)`
   - Active policy set to `set_interest_rate:2.5`
   - Generation = 1
   - Bond refunded
   - Global state: CONSENSUS_REACHED → OBSERVING
   - Cooldown timer starts

### What This Proves

- Full lifecycle works
- Data is fetched from the internet
- Validators reach consensus
- Policy is live and queryable

### Verification

- `get_active_policy()` returns the executed policy
- `get_history()` shows one entry with rationale
- Contract events visible on explorer

## Scenario 2: Rejection Path — Bad Policy Blocked

Purpose: Show that the consensus layer rejects harmful or unsupported
proposals.

### Precondition

- Cooldown from Scenario 1 has elapsed (demo script waits)
- Global state is OBSERVING

### Narrative

An observation shows stable economic conditions. A proposer tries to
push an extreme rate hike anyway. Validators reject it.

### Steps

1. **Fetch data**
   - Caller invokes `fetch_data(["https://www.reuters.com/markets/"])`
   - Observation stored with an LLM-generated summary
   - Returns observation_id = 2

2. **Propose extreme policy**
   - Caller invokes `propose_policy(2, "set_interest_rate:18", 100)`
   - Direction is within bounds (18 < 20), so it passes the guard
   - Bond locked
   - Global state: OBSERVING → POLICY_PROPOSED

3. **Evaluate**
   - Caller invokes `evaluate_policy(2)`
   - Validators read observation + direction
   - Verdict: REJECTED
   - Rationale: LLM-generated reasoning (illustrative)
   - Global state: POLICY_PROPOSED → CONSENSUS_FAILED

4. **Finalize failure**
   - Caller invokes `finalize_failed(2)`
   - Bond slashed
   - Global state: CONSENSUS_FAILED → OBSERVING
   - Active policy unchanged
   - Cooldown timer starts

### What This Proves

- Consensus rejects unsupported policies
- Bonds are slashed for bad proposals
- Active policy is not corrupted by spam
- Safety bounds alone are not enough — consensus adds judgment

### Verification

- `get_active_policy()` unchanged from Scenario 1
- `get_history()` shows a REJECTED entry with rationale
- Proposer's bond is gone

## Scenario 3: Emergency Pause — Admin Halt

Purpose: Show the admin kill switch works without affecting policy
decisions.

### Precondition

- Cooldown from Scenario 2 has elapsed
- Global state is OBSERVING

### Narrative

An admin sees suspicious activity and pauses the contract. No new
proposals can be made. Unpause resumes normal operation.

### Steps

1. **Pause**
   - Admin invokes `pause()`
   - Global state: OBSERVING → EMERGENCY_PAUSED

2. **Attempt proposal during pause**
   - Caller invokes `fetch_data([...])`
   - Reverts with INVALID_STATE
   - Caller invokes `propose_policy(...)`
   - Reverts with INVALID_STATE

3. **Unpause**
   - Admin invokes `unpause()`
   - Global state: EMERGENCY_PAUSED → OBSERVING

4. **Resume normal flow**
   - Caller invokes `fetch_data(["https://www.reuters.com/markets/"])`
   - Succeeds
   - Full lifecycle can now run

### What This Proves

- Admin can halt the system
- Admin cannot propose or modify policy
- Halt is reversible
- No proposals can be forced through during pause

### Verification

- `get_global_state()` shows EMERGENCY_PAUSED then OBSERVING
- No policy was executed during pause
- Events emitted for Paused and Unpaused
- Contract events visible on explorer

## Scenario 4 (Optional): Malformed Direction Rejection

Purpose: Show input validation.

### Precondition

- Fresh observation exists (observation_id = 3)
- Global state is OBSERVING
- Cooldown has elapsed

### Narrative

A caller submits a malformed direction string. The contract rejects
it before any bond is locked.

### Steps

1. **Propose malformed direction**
   - Caller invokes `propose_policy(3, "make_it_rain", 100)`
   - Reverts with INVALID_DIRECTION
   - No bond locked
   - State unchanged

2. **Propose out-of-bounds value**
   - Caller invokes `propose_policy(3, "set_interest_rate:50", 100)`
   - Reverts with OUT_OF_BOUNDS
   - No bond locked

### What This Proves

- Input validation works
- Bounds are enforced
- No bond is wasted on bad inputs

## Demo Video Structure

Total runtime: 5-7 minutes.

1. **Intro (30s)** — Problem and positioning
2. **Scenario 1 (2 min)** — Happy path with live contract
3. **Scenario 2 (2 min)** — Rejection path
4. **Scenario 3 (1 min)** — Emergency pause
5. **Outro (30s)** — What this enables, who uses it

## What the Demo Does NOT Show

- Real money movements (simulated bond only)
- Mainnet deployment (Studionet only)
- Integration with real stablecoins (roadmap)
- Governance upgrades (roadmap)
- Multi-asset policy (roadmap)

These are honest limitations. Mention them explicitly in the video
outro.

## Reproducibility

All scenarios run on GenLayer Studionet. The exact commands will be
in `scripts/demo.sh` (to be written). Contract addresses will be
published in the README.

The demo deploy uses a shortened cooldown (10 seconds) so scenarios
can run back-to-back. Production deployments would use a longer
cooldown.

Anyone can re-run the scenarios and verify the outcomes.