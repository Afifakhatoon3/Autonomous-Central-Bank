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

### `fetch_data(sources: list[str]) -> int`

Reads real-world data from the internet and stores it.

- Permissionless. Anyone can call.
- Reverts if global state is not OBSERVING.
- Uses GenLayer's Intelligent Oracle to fetch URLs.
- Creates a structured Observation object:
  - observation_id (auto-incrementing)
  - source_urls
  - fetched_at (timestamp)
  - summary (LLM-generated summary of the data)
- Appends the observation to `observations[]`.
- Updates `latest_observation` to point to the new observation.
- Returns the new `observation_id`.
- Emits `DataFetched` event.

Note: This method does not propose policy. It only gathers data.
Note: Data can be stale. `propose_policy()` should reject observations
older than a configurable freshness window (default: 1 hour).

## 3. Proposal Methods

### `propose_policy(observation_id: int, direction: str, bond: int)`

Creates a new policy proposal.

- Permissionless. Anyone can call.
- Reverts if:
  - State is not OBSERVING
  - Cooldown is still active
  - `observation_id` does not exist
  - Observation is stale (older than freshness window)
  - `bond` is below the minimum required bond
  - Direction is outside safety bounds
- Locks the bond in a simulated ledger (testnet MVP).
- Stores a new proposal in `proposals[]` with state PROPOSED.
- Transitions global state OBSERVING → POLICY_PROPOSED.
- Emits `PolicyProposed` event.

Parameters:
- `observation_id`: reference to a stored observation
- `direction`: policy direction, e.g. "increase_interest_rate:2.5"
- `bond`: bond amount in simulated GEN (testnet MVP)

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
- Inside this single call:
  1. Global state POLICY_PROPOSED → CONSENSUS_PENDING
  2. Per-policy state PROPOSED → EVALUATING
  3. Calls `gl.nondet.exec_prompt()` with the observation summary
     and the proposed direction
  4. GenLayer validators reach consensus on the verdict
  5. Based on verdict:
     - ACCEPTED → per-policy EVALUATING → ACCEPTED
       global CONSENSUS_PENDING → CONSENSUS_REACHED
     - REJECTED → per-policy EVALUATING → REJECTED
       global CONSENSUS_PENDING → CONSENSUS_FAILED
     - INCONCLUSIVE → per-policy EVALUATING → INCONCLUSIVE
       global CONSENSUS_PENDING → CONSENSUS_FAILED
- Emits `PolicyEvaluated` event with the verdict and rationale.

Note: CONSENSUS_PENDING is transient. It exists only during the
execution of this call. Observers reading state after the call will
see either CONSENSUS_REACHED or CONSENSUS_FAILED.

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

### `get_observation(observation_id: int) -> dict`

Returns a specific observation by ID.

### `get_bounds() -> dict`

Returns the immutable safety bounds.

## Method Summary Table

| Method | Who | Reverts if | Changes state |
|---|---|---|---|
| __init__ | Deployer | Once only | INIT |
| observe | Anyone | Not INIT | INIT → OBSERVING |
| pause | Admin | Already paused | Any → EMERGENCY_PAUSED |
| unpause | Admin | Not paused | EMERGENCY_PAUSED → OBSERVING |
| fetch_data | Anyone | Not OBSERVING | Appends to observations[] |
| propose_policy | Anyone | Cooldown, bounds, bond, state, stale observation | OBSERVING → POLICY_PROPOSED |
| cancel_proposal | Proposer | Not POLICY_PROPOSED | POLICY_PROPOSED → OBSERVING |
| evaluate_policy | Anyone | Not POLICY_PROPOSED | POLICY_PROPOSED → CONSENSUS_PENDING → CONSENSUS_REACHED or CONSENSUS_FAILED (same call) |
| execute_policy | Anyone | Not CONSENSUS_REACHED | CONSENSUS_REACHED → POLICY_EXECUTED → OBSERVING |
| finalize_failed | Anyone | Not CONSENSUS_FAILED | CONSENSUS_FAILED → OBSERVING |
| get_* | Anyone | Never | None |

## Edge Cases

| Case | Behavior |
|---|---|
| propose_policy() called with no observation | Reverts with NO_OBSERVATION error |
| propose_policy() called with stale observation | Reverts with STALE_OBSERVATION error |
| fetch_data() called outside OBSERVING | Reverts with INVALID_STATE error |
| evaluate_policy() called twice on same proposal | Second call reverts with ALREADY_EVALUATED |
| Bond below minimum | Reverts with BOND_TOO_LOW |

## What This API Does Not Do

- No admin override of consensus decisions
- No token mint or burn
- No fund transfer to any party
- No upgradeable logic in MVP
- No hidden state mutation

Every method has one job. Every state change is visible. Every decision is stored.