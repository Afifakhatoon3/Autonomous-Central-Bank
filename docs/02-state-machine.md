# State Machine Design

## Overview

The Autonomous Central Bank (ACB) operates as a continuous loop. It
observes real-world data, proposes policy changes, reaches consensus,
and executes. No human vote at any step.

## States

The contract has one global lifecycle state and one per-policy state.

### Global Lifecycle State