# Weaknesses and Fixes

## Overview

This document is an honest audit of the Autonomous Central Bank (ACB). It lists every known weakness, the fix applied or planned, and the status. Nothing is hidden.

This is the document reviewers should read first.

## Weakness Categories

1. Design weaknesses - fixed in the design
2. Economic weaknesses - accepted for MVP, roadmap for v2
3. Technical weaknesses - partially mitigated
4. Adoption weaknesses - out of scope, roadmap
5. Demo weaknesses - explicitly documented
6. Architectural weaknesses - accepted by design

## 1. Design Weaknesses

### W1: Single bad LLM decision could break the system

Risk: An LLM might ACCEPT a harmful policy or REJECT a good one.

Fix: Three layers of defense.
- Layer 1: Immutable safety bounds reject out-of-range proposals
  before consensus
- Layer 2: Consensus across multiple validators
- Layer 3: INCONCLUSIVE verdict when validators disagree

Status: Fixed.

### W2: Admin could abuse the pause function

Risk: Admin pauses the contract forever, blocking all proposals.

Fix: Admin can only pause, not decide. Unpause is always available. The contract stores `state_before_pause` and restores it on unpause, so any in-flight policy (e.g. CONSENSUS_REACHED) is preserved, not dropped. Policy decisions are not affected. Admin cannot propose, cancel, or modify any proposal.

Status: Fixed in design. Trust assumption on admin for MVP remains.
Roadmap: replace admin with multi-sig or timelock.

### W3: Proposals could be spammed

Risk: Anyone can call propose_policy() repeatedly.

Fix: Two guards.
- Cooldown between proposals
- Proposal bond (slashed on REJECTED, refunded on ACCEPTED or
  INCONCLUSIVE)

Status: Fixed.

### W4: Observations could be stale

Risk: A proposal uses an old observation that no longer reflects reality.

Fix: Freshness window (default 1 hour). Stale observations are
rejected with STALE_OBSERVATION error.

Status: Fixed.

### W5: Malformed direction strings

Risk: Caller submits garbage that the contract cannot parse.

Fix: Strict format `<parameter>:<value>`. Invalid formats revert with INVALID_DIRECTION before any bond is locked.

Status: Fixed.

## 2. Economic Weaknesses

### W6: Bond value is arbitrary

Risk: The minimum bond is set by the deployer. It may be too low (spam) or too high (exclusion).

Fix: Bond is configurable at deploy. MVP uses a simulated value.
Roadmap: dynamic bond based on proposal volume.

Status: Accepted.

### W7: No pricing mechanism for bonds

Risk: Bond slashing is binary. There is no economic model that
balances spam prevention against accessibility.

Fix: None for MVP. Roadmap: study bond curves used by prediction markets and insurance protocols.

Status: Roadmap.

### W8: Simulated bond has no real value

Risk: On testnet, bonds are simulated. There is no real economic cost to proposing bad policies.

Fix: Accepted. Real bond requires real token integration, which is out of scope for MVP.

Status: Accepted.

### W9: Policy does not move real money

Risk: The ACB outputs policy decisions, but does not execute them on any stablecoin. The link between policy and economic effect is narrative, not mechanical.

Fix: Explicitly positioned as a policy engine, not a stablecoin. The README states this. Roadmap: integration with a real stablecoin protocol.

Status: Accepted and documented.

## 3. Technical Weaknesses

### W10: LLM output is not deterministic

Risk: The same observation and direction could yield different
verdicts across runs.

Fix: GenLayer's equivalence principle ensures semantic agreement, not byte-identical output. The verdict is ACCEPTED, REJECTED, or INCONCLUSIVE - a small, discrete set. Consensus makes the outcome stable.

Status: Mitigated by design.

### W11: Source authenticity is not verified

Risk: A caller could submit a URL whose content is fabricated.

Fix: Source authenticity is the caller's responsibility. The bond disincentivizes spam. Roadmap: allowlist of trusted news sources or signature-based verification.

Status: Accepted for MVP. Documented in Trust Assumptions.

### W12: Observation summary is compressed

Risk: The LLM summary loses nuance. A 5,000-word article becomes 200 words. Important context may be lost.

Fix: None for MVP. Roadmap: keep full source text on IPFS and pass hash to the contract, so validators can fetch and verify.

Status: Roadmap.

### W13: No appeal mechanism for rejected proposals

Risk: A good proposal rejected by mistake cannot be appealed.

Fix: A rejected proposal can be re-proposed after cooldown, provided the observation is still fresh. There is no formal appeal.

Status: Accepted. Roadmap: multi-round adjudication.

### W14: evaluate_policy is atomic but expensive

Risk: Consensus across multiple validators is the most expensive operation in the contract.

Fix: None. This is inherent to GenLayer's design. Accepted as a cost of doing subjective consensus on-chain.

Status: Accepted.

### W15: No upgrade path

Risk: If a bug is found in the contract, there is no way to patch it.

Fix: None for MVP. Roadmap: proxy pattern with timelocked upgrades under multi-sig governance.

Status: Roadmap.

### W24: Some URLs blocked by bot protection

Risk: News sites like Reuters, Bloomberg, WSJ return 401 to
automated requests. The Intelligent Oracle cannot fetch them.

Fix: fetch_data uses try/except per URL. If all sources fail, the call reverts with NO_DATA_FETCHED. Supported sources documented as Wikipedia, public RSS feeds, and APIs without bot protection.

Status: Handled defensively.

### W25: LLM reasoning tags could leak into summaries

Risk: Some models include <think> or <reasoning> tags in output, polluting the observation summary.

Fix: Explicit "CRITICAL OUTPUT RULES" added to the summary prompt (forbidding XML tags, reasoning tags, meta commentary). Defensive post-processing strips any leaked tags. Equivalence criteria also enforces tag-free output.

Status: Fixed and verified on Studionet.

### W26: Empty summary would silently pass

Risk: If all URLs failed, summary would be empty string, and
evaluate_policy would return INCONCLUSIVE with a confusing reason.

Fix: fetch_data now reverts with NO_DATA_FETCHED if summary is empty. No observation is stored for failed fetches.

Status: Fixed.

### W27: get_history unbounded growth

Risk: get_history iterated all proposals, becoming expensive as proposal_counter grew.

Fix: get_history now accepts offset and limit parameters. Added get_proposal_count() for pagination support.

Status: Fixed.

## 4. Adoption Weaknesses

### W16: No live consumers

Risk: The ACB outputs policy decisions, but no stablecoin, DAO, or agent reads them yet.

Fix: None for MVP. The project is a primitive, not a product.
Adoption requires integration work that is out of scope.

Status: Accepted and documented.

### W17: No clear distribution channel

Risk: Even with a strong primitive, reaching the right users is unclear.

Fix: Roadmap includes three channels:
1. Direct integration with existing GenLayer ecosystem projects
2. Public SDK for stablecoin protocols
3. Governance forum outreach for DAOs with stablecoin treasuries

Status: Roadmap.

### W18: Regulatory uncertainty

Risk: Autonomous monetary policy may attract regulatory scrutiny if connected to a real stablecoin.

Fix: The ACB is positioned as a policy engine, not a currency issuer. It does not custody funds, mint tokens, or transact with users.

Status: Accepted and documented.

## 5. Demo Weaknesses

### W19: Verdicts are illustrative

Risk: The demo script expects specific verdicts (ACCEPTED, REJECTED, INCONCLUSIVE). Actual LLM output may differ.

Fix: The demo script handles all three verdicts. The narrative
describes the mechanism, not a scripted result.

Status: Documented.

### W20: Cooldown breaks back-to-back scenarios

Risk: Scenario 2 cannot run immediately after Scenario 1 because of the cooldown.

Fix: The demo deployment uses a shortened cooldown (10 seconds). The README documents this deviation from production parameters.

Status: Documented.

### W21: URLs are real but generic

Risk: The demo uses real URLs, but content changes daily.

Fix: Accepted. The demo shows the mechanism, not a specific news event. The verdict may change based on current news. This is a feature, not a bug.

Status: Documented.

## 6. Architectural Weaknesses

### W22: Only one in-flight proposal at a time

Risk: The global state machine allows only one proposal to be active at any moment. Parallel proposals are not supported.

Fix: None. This is by design. A single policy pipeline keeps the state machine simple and prevents race conditions. Roadmap:
multi-lane proposals if adoption requires it.

Status: Accepted by design.

### W23: Data fetching blocked outside OBSERVING

Risk: While a proposal is in POLICY_PROPOSED, CONSENSUS_PENDING, or CONSENSUS_REACHED, no new observations can be fetched.

Fix: None. This is by design. It prevents stale or conflicting
observations from entering the pipeline mid-decision. Roadmap:
allow observation buffering during non-OBSERVING states.

Status: Accepted by design.

## Summary Table

| Weakness | Severity | Status |
|---|---|---|
| W1 Single bad LLM decision | High | Fixed |
| W2 Admin abuse | Medium | Fixed in design |
| W3 Spam proposals | High | Fixed |
| W4 Stale observations | Medium | Fixed |
| W5 Malformed direction | Low | Fixed |
| W6 Arbitrary bond value | Medium | Accepted |
| W7 No bond pricing | Low | Roadmap |
| W8 Simulated bond | Medium | Accepted |
| W9 No real money | High | Accepted and documented |
| W10 LLM non-determinism | Medium | Mitigated |
| W11 Source authenticity | Medium | Accepted |
| W12 Summary compression | Low | Roadmap |
| W13 No appeal | Medium | Accepted |
| W14 Expensive evaluation | Low | Accepted |
| W15 No upgrade path | Medium | Roadmap |
| W16 No live consumers | High | Accepted and documented |
| W17 No distribution | High | Roadmap |
| W18 Regulatory risk | Medium | Accepted |
| W19 Verdict variability | Low | Documented |
| W20 Cooldown in demo | Low | Documented |
| W21 Dynamic URLs | Low | Documented |
| W22 Single in-flight proposal | Medium | Accepted by design |
| W23 Data fetch blocked during processing | Medium | Accepted by design |
| W24 URL bot protection | Low | Handled |
| W25 LLM reasoning tags | Low | Fixed |
| W26 Empty summary silent pass | Medium | Fixed |
| W27 get_history unbounded | Low | Fixed |

## What This Document Proves

- Every weakness is known and named.
- Fixes are applied where possible.
- Accepted limitations are documented, not hidden.
- Roadmap items are scoped, not hand-waved.

This is the level of honesty expected from a system that claims to run without human intervention.