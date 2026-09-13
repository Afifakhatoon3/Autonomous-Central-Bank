# State Machine Design

## Overview

The Autonomous Central Bank (ACB) operates as a continuous loop. It
observes real-world data, proposes policy changes, reaches consensus,
and executes. No human vote at any step.

## States

The contract has one global lifecycle state and one per-policy state.

### Global Lifecycle State

```

INIT

|
v
OBSERVING <-----------------------+

|                               |
v                               |
POLICY_PROPOSED                   |

|                               |
v                               |
CONSENSUS_PENDING                 |

|                               |
+--> CONSENSUS_REACHED          |

|         |                     |

|         v                     |
|    POLICY_EXECUTED -----------+

|                               |
+--> CONSENSUS_FAILED ----------+

|
+--> EMERGENCY_PAUSED

```


| State | Meaning |
|---|---|
| INIT | Contract deployed, no policy yet. First observe() expected. |
| OBSERVING | Waiting for next observation cycle. Cooldown active. |
| POLICY_PROPOSED | A policy proposal exists, awaiting consensus. |
| CONSENSUS_PENDING | Validators are evaluating the proposal. |
| CONSENSUS_REACHED | Validators agreed on a policy direction. |
| POLICY_EXECUTED | Policy applied. Returns to OBSERVING. |
| CONSENSUS_FAILED | Validators disagreed or confidence too low. Returns to OBSERVING. |
| EMERGENCY_PAUSED | Admin halted the contract. No proposals accepted. |

### Per-Policy State

Each policy proposal has its own state, tracked in a history array.

```

PROPOSED --> EVALUATING --> ACCEPTED --> EXECUTED
--> REJECTED
--> INCONCLUSIVE

```

| State | Meaning |
|---|---|
| PROPOSED | Proposal created, evidence attached. |
| EVALUATING | Validators fetching evidence and judging. |
| ACCEPTED | Consensus reached, policy is valid. |
| REJECTED | Consensus says policy is harmful or unsupported. |
| INCONCLUSIVE | Validators could not agree. |
| EXECUTED | Accepted policy written to live state. |

## Transitions

| From | To | Trigger | Who |
|---|---|---|---|
| INIT | OBSERVING | First observe() call | Anyone |
| OBSERVING | POLICY_PROPOSED | propose_policy() after cooldown | Anyone |
| POLICY_PROPOSED | CONSENSUS_PENDING | evaluate_policy() called | Anyone |
| CONSENSUS_PENDING | CONSENSUS_REACHED | Validators return ACCEPTED | GenLayer consensus |
| CONSENSUS_PENDING | CONSENSUS_FAILED | Validators return REJECTED or INCONCLUSIVE | GenLayer consensus |
| CONSENSUS_REACHED | POLICY_EXECUTED | execute_policy() called | Anyone |
| POLICY_EXECUTED | OBSERVING | Automatic | Contract |
| CONSENSUS_FAILED | OBSERVING | Automatic | Contract |
| Any | EMERGENCY_PAUSED | pause() called | Admin only |
| EMERGENCY_PAUSED | OBSERVING | unpause() called | Admin only |

## Guards and Constraints

- **Cooldown:** After a policy executes or fails, a minimum number of
  blocks must pass before the next propose_policy() call.
- **Policy bounds:** Every proposed policy must fall within predefined
  safety ranges. Out-of-range proposals are rejected before consensus.
- **Proposal bond:** Each propose_policy() call requires a small bond.
  If the proposal is rejected as spam, the bond is slashed.
- **Admin scope:** The admin can only pause and unpause. The admin
  cannot propose, reject, or modify policy decisions.

## Safety Bounds (Example)

These are configured at deploy time and are immutable.

| Parameter | Min | Max |
|---|---|---|
| Interest rate | 0% | 20% |
| Collateral ratio | 100% | 200% |
| Supply adjustment | -5% | +5% per cycle |

Any proposal outside these bounds is rejected immediately without
consensus. This prevents a single bad LLM output from breaking the
system.

## What This State Machine Prevents

| Risk | How it is prevented |
|---|---|
| Single bad LLM decision | Consensus across multiple validators |
| Spam proposals | Cooldown + proposal bond |
| Extreme policy shifts | Immutable safety bounds |
| Admin takeover | Admin can only pause, not decide |
| Silent policy change | Every transition emits an event and is stored |
| Infinite loop of proposals | Cooldown between cycles |
```

---
