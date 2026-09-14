# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

from genlayer import *
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import typing


@allow_storage
@dataclass
class Observation:
    observation_id: u256
    source_urls: str
    fetched_at: u256
    summary: str


@allow_storage
@dataclass
class Proposal:
    proposal_id: u256
    proposer: Address
    observation_id: u256
    direction: str
    bond: u256
    created_at: u256
    state: str
    verdict: str
    rationale: str


@allow_storage
@dataclass
class HistoryEntry:
    proposal_id: u256
    direction: str
    verdict: str
    rationale: str
    evaluated_at: u256


class AutonomousCentralBank(gl.Contract):
    admin: Address
    global_state: str
    state_before_pause: str

    interest_min: u256
    interest_max: u256
    collateral_min: u256
    collateral_max: u256
    supply_min: i256
    supply_max: i256

    cooldown_seconds: u256
    min_bond: u256
    freshness_seconds: u256

    observations: TreeMap[u256, Observation]
    proposals: TreeMap[u256, Proposal]
    history: TreeMap[u256, HistoryEntry]
    bonds: TreeMap[Address, u256]

    observation_counter: u256
    proposal_counter: u256
    generation: u256

    active_direction: str
    active_observation_id: u256
    active_executed_at: u256
    last_policy_timestamp: u256

    def __init__(self) -> None:
        self.admin = gl.message.sender_address
        self.global_state = "INIT"
        self.state_before_pause = ""

        self.interest_min = u256(0)
        self.interest_max = u256(20000)
        self.collateral_min = u256(100000)
        self.collateral_max = u256(200000)
        self.supply_min = i256(-5000)
        self.supply_max = i256(5000)

        self.cooldown_seconds = u256(10)
        self.min_bond = u256(100)
        self.freshness_seconds = u256(3600)

        self.observation_counter = u256(0)
        self.proposal_counter = u256(0)
        self.generation = u256(0)

        self.active_direction = ""
        self.active_observation_id = u256(0)
        self.active_executed_at = u256(0)
        self.last_policy_timestamp = u256(0)

    def _now(self) -> int:
        return int(datetime.now(timezone.utc).timestamp())

    def _require_admin(self) -> None:
        if gl.message.sender_address != self.admin:
            raise gl.vm.UserError("NOT_ADMIN")

    def _parse_milli(self, value_str: str) -> int:
        value_str = value_str.strip()
        is_negative = value_str.startswith('-')
        if is_negative:
            value_str = value_str[1:]
        if '.' in value_str:
            parts = value_str.split('.')
            whole_str = parts[0]
            frac_str = parts[1]
        else:
            whole_str = value_str
            frac_str = '0'
        frac_str = (frac_str + '000')[:3]
        whole = int(whole_str) if whole_str else 0
        frac = int(frac_str)
        result = whole * 1000 + frac
        return -result if is_negative else result

    def _parse_direction(self, direction: str) -> typing.Tuple[str, int]:
        if ':' not in direction:
            raise gl.vm.UserError("INVALID_DIRECTION")
        parts = direction.split(':', 1)
        key = parts[0].strip()
        value_str = parts[1].strip()
        allowed = ("set_interest_rate", "set_collateral_ratio", "set_supply_adjustment")
        if key not in allowed:
            raise gl.vm.UserError("INVALID_DIRECTION")
        value_milli = self._parse_milli(value_str)
        return key, value_milli

    def _check_bounds(self, key: str, value_milli: int) -> None:
        if key == "set_interest_rate":
            if value_milli < int(self.interest_min) or value_milli > int(self.interest_max):
                raise gl.vm.UserError("OUT_OF_BOUNDS")
        elif key == "set_collateral_ratio":
            if value_milli < int(self.collateral_min) or value_milli > int(self.collateral_max):
                raise gl.vm.UserError("OUT_OF_BOUNDS")
        elif key == "set_supply_adjustment":
            if value_milli < int(self.supply_min) or value_milli > int(self.supply_max):
                raise gl.vm.UserError("OUT_OF_BOUNDS")

    @gl.public.write
    def observe(self) -> None:
        if self.global_state != "INIT":
            raise gl.vm.UserError("INVALID_STATE")
        self.global_state = "OBSERVING"

    @gl.public.write
    def pause(self) -> None:
        self._require_admin()
        if self.global_state == "EMERGENCY_PAUSED":
            raise gl.vm.UserError("ALREADY_PAUSED")
        self.state_before_pause = self.global_state
        self.global_state = "EMERGENCY_PAUSED"

    @gl.public.write
    def unpause(self) -> None:
        self._require_admin()
        if self.global_state != "EMERGENCY_PAUSED":
            raise gl.vm.UserError("NOT_PAUSED")
        self.global_state = self.state_before_pause
        self.state_before_pause = ""

    @gl.public.write
    def fetch_data(self, sources: str) -> u256:
        if self.global_state != "OBSERVING":
            raise gl.vm.UserError("INVALID_STATE")
        urls = json.loads(sources)
        if not isinstance(urls, list) or len(urls) == 0:
            raise gl.vm.UserError("INVALID_SOURCES")
        for url in urls:
            if not isinstance(url, str) or not url.startswith("https://"):
                raise gl.vm.UserError("INVALID_SOURCES")

        def fetch_and_summarize() -> str:
            all_text = ""
            for url in urls:
                text = gl.nondet.web.render(url, mode="text")
                all_text += f"\n\n--- Source: {url} ---\n{text[:3000]}"
            task = (
                "Summarize the following sources in 3-5 sentences. "
                "Focus on economic signals relevant to monetary policy. "
                "Respond with only the summary text.\n\nSources:\n" + all_text
            )
            result = gl.nondet.exec_prompt(task)
            return result.strip()

        summary = gl.eq_principle.prompt_non_comparative(
            fetch_and_summarize,
            task="Summarize economic sources",
            criteria="Must return a non-empty text summary focused on economic signals",
        )

        self.observation_counter = self.observation_counter + u256(1)
        obs_id = self.observation_counter
        obs = Observation(
            observation_id=obs_id,
            source_urls=json.dumps(urls),
            fetched_at=u256(self._now()),
            summary=summary,
        )
        self.observations[obs_id] = obs
        return obs_id

    @gl.public.write
    def propose_policy(self, observation_id: u256, direction: str, bond: u256) -> u256:
        if self.global_state != "OBSERVING":
            raise gl.vm.UserError("INVALID_STATE")

        now = self._now()
        if now - int(self.last_policy_timestamp) < int(self.cooldown_seconds):
            raise gl.vm.UserError("COOLDOWN_ACTIVE")

        if observation_id not in self.observations:
            raise gl.vm.UserError("NO_OBSERVATION")

        obs = self.observations[observation_id]
        if now - int(obs.fetched_at) > int(self.freshness_seconds):
            raise gl.vm.UserError("STALE_OBSERVATION")

        if int(bond) < int(self.min_bond):
            raise gl.vm.UserError("BOND_TOO_LOW")

        key, value_milli = self._parse_direction(direction)
        self._check_bounds(key, value_milli)

        sender = gl.message.sender_address
        current_bond = int(self.bonds.get(sender, u256(0)))
        self.bonds[sender] = u256(current_bond + int(bond))

        self.proposal_counter = self.proposal_counter + u256(1)
        prop_id = self.proposal_counter
        prop = Proposal(
            proposal_id=prop_id,
            proposer=sender,
            observation_id=observation_id,
            direction=direction,
            bond=bond,
            created_at=u256(now),
            state="PROPOSED",
            verdict="",
            rationale="",
        )
        self.proposals[prop_id] = prop
        self.global_state = "POLICY_PROPOSED"
        return prop_id

    @gl.public.write
    def cancel_proposal(self, proposal_id: u256) -> None:
        if self.global_state != "POLICY_PROPOSED":
            raise gl.vm.UserError("INVALID_STATE")
        if proposal_id not in self.proposals:
            raise gl.vm.UserError("NO_PROPOSAL")
        prop = self.proposals[proposal_id]
        if prop.proposer != gl.message.sender_address:
            raise gl.vm.UserError("NOT_PROPOSER")
        sender = prop.proposer
        current_bond = int(self.bonds.get(sender, u256(0)))
        self.bonds[sender] = u256(current_bond - int(prop.bond))
        prop.state = "CANCELLED"
        self.proposals[proposal_id] = prop
        self.global_state = "OBSERVING"

    @gl.public.write
    def evaluate_policy(self, proposal_id: u256) -> None:
        if self.global_state != "POLICY_PROPOSED":
            raise gl.vm.UserError("INVALID_STATE")
        if proposal_id not in self.proposals:
            raise gl.vm.UserError("NO_PROPOSAL")

        prop = self.proposals[proposal_id]
        if prop.state != "PROPOSED":
            raise gl.vm.UserError("ALREADY_EVALUATED")

        obs = self.observations[prop.observation_id]
        summary = obs.summary
        direction = prop.direction

        self.global_state = "CONSENSUS_PENDING"
        prop.state = "EVALUATING"
        self.proposals[proposal_id] = prop

        task = (
            "You are an autonomous monetary policy evaluator.\n\n"
            "Observation summary:\n" + summary + "\n\n"
            "Proposed policy: " + direction + "\n\n"
            "Evaluate whether this proposed policy is appropriate. "
            "Respond with valid JSON only: "
            '{"verdict": "ACCEPTED" or "REJECTED" or "INCONCLUSIVE", '
            '"rationale": "Brief explanation in one sentence"}\n\n'
            "Rules:\n"
            "- ACCEPTED: The observation supports the policy and magnitude\n"
            "- REJECTED: The observation contradicts the policy or magnitude is unreasonable\n"
            "- INCONCLUSIVE: The observation is ambiguous or insufficient"
        )

        def leader_fn() -> dict:
            result = gl.nondet.exec_prompt(task, response_format="json")
            return result

        def validator_fn(leader_result) -> bool:
            if not isinstance(leader_result, gl.vm.Return):
                return False
            data = leader_result.calldata
            if not isinstance(data, dict):
                return False
            verdict = data.get("verdict", "")
            if verdict not in ("ACCEPTED", "REJECTED", "INCONCLUSIVE"):
                return False
            rationale = data.get("rationale", "")
            if not isinstance(rationale, str) or len(rationale.strip()) == 0:
                return False
            return True

        result = gl.vm.run_nondet_unsafe(leader_fn, validator_fn)
        verdict = result["verdict"]
        rationale = result["rationale"]

        prop = self.proposals[proposal_id]
        prop.verdict = verdict
        prop.rationale = rationale

        if verdict == "ACCEPTED":
            prop.state = "ACCEPTED"
            self.global_state = "CONSENSUS_REACHED"
        else:
            prop.state = verdict
            self.global_state = "CONSENSUS_FAILED"

        self.proposals[proposal_id] = prop

    @gl.public.write
    def execute_policy(self, proposal_id: u256) -> None:
        if self.global_state != "CONSENSUS_REACHED":
            raise gl.vm.UserError("INVALID_STATE")
        if proposal_id not in self.proposals:
            raise gl.vm.UserError("NO_PROPOSAL")
        prop = self.proposals[proposal_id]
        if prop.state != "ACCEPTED":
            raise gl.vm.UserError("NOT_ACCEPTED")

        now = self._now()
        self.active_direction = prop.direction
        self.active_observation_id = prop.observation_id
        self.active_executed_at = u256(now)
        self.generation = self.generation + u256(1)
        self.last_policy_timestamp = u256(now)

        entry = HistoryEntry(
            proposal_id=proposal_id,
            direction=prop.direction,
            verdict=prop.verdict,
            rationale=prop.rationale,
            evaluated_at=u256(now),
        )
        self.history[proposal_id] = entry

        sender = prop.proposer
        current_bond = int(self.bonds.get(sender, u256(0)))
        self.bonds[sender] = u256(current_bond - int(prop.bond))

        prop.state = "EXECUTED"
        self.proposals[proposal_id] = prop
        self.global_state = "OBSERVING"

    @gl.public.write
    def finalize_failed(self, proposal_id: u256) -> None:
        if self.global_state != "CONSENSUS_FAILED":
            raise gl.vm.UserError("INVALID_STATE")
        if proposal_id not in self.proposals:
            raise gl.vm.UserError("NO_PROPOSAL")
        prop = self.proposals[proposal_id]

        now = self._now()
        entry = HistoryEntry(
            proposal_id=proposal_id,
            direction=prop.direction,
            verdict=prop.verdict,
            rationale=prop.rationale,
            evaluated_at=u256(now),
        )
        self.history[proposal_id] = entry

        sender = prop.proposer
        if prop.verdict == "INCONCLUSIVE":
            current_bond = int(self.bonds.get(sender, u256(0)))
            self.bonds[sender] = u256(current_bond - int(prop.bond))

        self.last_policy_timestamp = u256(now)
        prop.state = "FINALIZED_FAILED"
        self.proposals[proposal_id] = prop
        self.global_state = "OBSERVING"

    @gl.public.view
    def get_global_state(self) -> str:
        return self.global_state

    @gl.public.view
    def get_active_policy(self) -> dict:
        return {
            "direction": self.active_direction,
            "based_on_observation": int(self.active_observation_id),
            "executed_at": int(self.active_executed_at),
            "generation": int(self.generation),
        }

    @gl.public.view
    def get_proposal(self, proposal_id: u256) -> dict:
        if proposal_id not in self.proposals:
            raise gl.vm.UserError("NO_PROPOSAL")
        prop = self.proposals[proposal_id]
        return {
            "proposal_id": int(prop.proposal_id),
            "proposer": prop.proposer.as_hex,
            "observation_id": int(prop.observation_id),
            "direction": prop.direction,
            "bond": int(prop.bond),
            "created_at": int(prop.created_at),
            "state": prop.state,
            "verdict": prop.verdict,
            "rationale": prop.rationale,
        }

    @gl.public.view
    def get_proposal_state(self, proposal_id: u256) -> str:
        if proposal_id not in self.proposals:
            raise gl.vm.UserError("NO_PROPOSAL")
        return self.proposals[proposal_id].state

    @gl.public.view
    def get_history(self) -> list:
        result = []
        for i in range(1, int(self.proposal_counter) + 1):
            if u256(i) in self.history:
                entry = self.history[u256(i)]
                result.append({
                    "proposal_id": int(entry.proposal_id),
                    "direction": entry.direction,
                    "verdict": entry.verdict,
                    "rationale": entry.rationale,
                    "evaluated_at": int(entry.evaluated_at),
                })
        return result

    @gl.public.view
    def get_observation(self, observation_id: u256) -> dict:
        if observation_id not in self.observations:
            raise gl.vm.UserError("NO_OBSERVATION")
        obs = self.observations[observation_id]
        return {
            "observation_id": int(obs.observation_id),
            "source_urls": obs.source_urls,
            "fetched_at": int(obs.fetched_at),
            "summary": obs.summary,
        }

    @gl.public.view
    def get_latest_observation(self) -> dict:
        if int(self.observation_counter) == 0:
            raise gl.vm.UserError("NO_OBSERVATION")
        return self.get_observation(self.observation_counter)

    @gl.public.view
    def get_bounds(self) -> dict:
        return {
            "interest_min": int(self.interest_min),
            "interest_max": int(self.interest_max),
            "collateral_min": int(self.collateral_min),
            "collateral_max": int(self.collateral_max),
            "supply_min": int(self.supply_min),
            "supply_max": int(self.supply_max),
        }

    @gl.public.view
    def get_bond(self, address_hex: str) -> int:
        addr = Address(address_hex)
        return int(self.bonds.get(addr, u256(0)))