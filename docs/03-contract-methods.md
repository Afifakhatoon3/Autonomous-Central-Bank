# Contract Methods

## Overview

The Autonomous Central Bank contract exposes a small, focused API. Every
method has one job. No method does two things.

Methods are grouped into five categories:

1. Lifecycle — start and maintain the contract
2. Observation — read real-world data
3. Proposal — create policy proposals
4. Consensus — evaluate and execute proposals
5. Views — read-only queries

## 1. Lifecycle Methods

### `__init__(admin: str, bounds: dict)`

Constructor. Runs once at deploy.

- Stores the admin address
- Stores immutable safety bounds
- Sets global state to INIT

### `observe()`

Transitions INIT → OBSERVING.

- Permissionless. Anyone can call.
- Reverts if state is not INIT.
- Emits `ObserveStarted` event.

### `pause()`

Transitions any state → EMERGENCY_PAUSED.

- Admin only.
- Reverts if already EMERGENCY_PAUSED.
- Emits `Paused` event.

### `unpause()`

Transitions EMERGENCY_PAUSED → OBSERVING.

- Admin only.
- Reverts if not EMERGENCY_PAUSED.
- Emits `Unpaused` event.

## 2. Observation Methods

### `fetch_data(sources: list[str])`

Reads real-world data from the internet.

- Permissionless. Anyone can call.
- Uses GenLayer's Intelligent Oracle to fetch URLs.
- Returns a structured `Observation` object:
  - source_urls
  - fetched_at (timestamp)
  - summary (LLM-generated summary of the data)
- Stores the observation in `latest_observation`.
- Emits `DataFetched` event.

Note: This method does not propose policy. It only gathers data.

## 3. Proposal Methods

### `propose_policy(observation_id: int, direction: str)`

Creates a new policy proposal.

- Permissionless. Anyone can call.
- Reverts if:
  - State is not OBSERVING
  - Cooldown is still active
  - Proposal bond not attached
  - Direction is outside safety bounds
- Stores a new proposal in `proposals[]` with state PROPOSED.
- Transitions global state OBSERVING → POLICY_PROPOSED.
- Emits `PolicyProposed` event.

Parameters:
- `observation_id`: reference to a stored observation
- `direction`: policy direction, e.g. "increase_interest_rate:2.5"

### `cancel_proposal(proposal_id: int)`

Cancels a proposal before evaluation.

- Only the original proposer can call.
- Reverts if state is not POLICY_PROPOSED.
- Refunds the proposal bond.
- Transitions global state POLICY_PROPOSED → OBSERVING.
- Emits `PolicyCancelled` event.

## 4. Consensus Methods

### `evaluate_policy(proposal_id: int)`

Triggers consensus evaluation.

- Permissionless. Anyone can call.
- Reverts if state is not POLICY_PROPOSED.
- Transitions global state POLICY_PROPOSED → CONSENSUS_PENDING.
- Sets per-policy state PROPOSED → EVALUATING.
- Calls `gl.nondet.exec_prompt()` to run the LLM evaluation.
- Uses GenLayer consensus to determine the verdict.
- Based on verdict:
  - ACCEPTED → per-policy state EVALUATING → ACCEPTED
    global state CONSENSUS_PENDING → CONSENSUS_REACHED
  - REJECTED → per-policy state EVALUATING → REJECTED
    global state CONSENSUS_PENDING → CONSENSUS_FAILED
  - INCONCLUSIVE → per-policy state EVALUATING → INCONCLUSIVE
    global state CONSENSUS_PENDING → CONSENSUS_FAILED
- Emits `PolicyEvaluated` event with the verdict and rationale.

### `execute_policy(proposal_id: int)`

Writes an accepted policy to the live state.

- Permissionless. Anyone can call.
- Reverts if:
  - Global state is not CONSENSUS_REACHED
  - Per-policy state is not ACCEPTED
  - Policy was already executed
- Writes the policy to `active_policy`.
- Sets per-policy state ACCEPTED → EXECUTED.
- Transitions global state CONSENSUS_REACHED → POLICY_EXECUTED,
  then automatically to OBSERVING.
- Refunds the proposal bond.
- Emits `PolicyExecuted` event.

### `finalize_failed(proposal_id: int)`

Cleans up a failed proposal.

- Permissionless. Anyone can call.
- Reverts if global state is not CONSENSUS_FAILED.
- Slashes the proposal bond if the verdict was REJECTED.
- Refunds the bond if the verdict was INCONCLUSIVE.
- Transitions global state CONSENSUS_FAILED → OBSERVING.
- Emits `PolicyFailed` event.

## 5. View Methods

### `get_global_state() -> str`

Returns the current global lifecycle state.

### `get_active_policy() -> dict`

Returns the current live policy.

### `get_proposal(proposal_id: int) -> dict`

Returns the full proposal record.

### `get_proposal_state(proposal_id: int) -> str`

Returns the per-policy state.

### `get_history() -> list[dict]`

Returns all past proposals with their final states and rationales.

### `get_latest_observation() -> dict`

Returns the most recent observation.

### `get_bounds() -> dict`

Returns the immutable safety bounds.

## Method Summary Table

| Method | Who | Reverts if | Changes state |
|---|---|---|---|
| __init__ | Deployer | Once only | INIT |
| observe | Anyone | Not INIT | INIT → OBSERVING |
| pause | Admin | Already paused | Any → EMERGENCY_PAUSED |
| unpause | Admin | Not paused | EMERGENCY_PAUSED → OBSERVING |
| fetch_data | Anyone | Never (view-like) | Updates latest_observation |
| propose_policy | Anyone | Cooldown, bounds, bond, state | OBSERVING → POLICY_PROPOSED |
| cancel_proposal | Proposer | Not POLICY_PROPOSED | POLICY_PROPOSED → OBSERVING |
| evaluate_policy | Anyone | Not POLICY_PROPOSED | POLICY_PROPOSED → CONSENSUS_PENDING |
| execute_policy | Anyone | Not CONSENSUS_REACHED | CONSENSUS_REACHED → POLICY_EXECUTED → OBSERVING |
| finalize_failed | Anyone | Not CONSENSUS_FAILED | CONSENSUS_FAILED → OBSERVING |
| get_* | Anyone | Never | None |

## What This API Does Not Do

- No admin override of consensus decisions
- No token mint or burn
- No fund transfer to any party
- No upgradeable logic in MVP
- No hidden state mutation

Every method has one job. Every state change is visible. Every decision is stored.