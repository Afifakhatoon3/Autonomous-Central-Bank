"""
Direct tests for AutonomousCentralBank contract.

These tests use gltest to run against a local GenVM instance.
Integration tests (with real LLMs) require Studionet via genlayer CLI.
"""

import pytest
from gltest import get_contract_factory
from gltest.assertions import tx_execution_succeeded


@pytest.fixture
def contract():
    factory = get_contract_factory("AutonomousCentralBank")
    return factory.deploy()


def test_initial_state_is_init(contract):
    assert contract.get_global_state() == "INIT"


def test_observe_transitions_to_observing(contract):
    contract.observe()
    assert contract.get_global_state() == "OBSERVING"


def test_observe_twice_reverts(contract):
    contract.observe()
    with pytest.raises(Exception, match="INVALID_STATE"):
        contract.observe()


def test_pause_unpause_restores_state(contract):
    contract.observe()
    assert contract.get_global_state() == "OBSERVING"
    contract.pause()
    assert contract.get_global_state() == "EMERGENCY_PAUSED"
    contract.unpause()
    assert contract.get_global_state() == "OBSERVING"


def test_pause_twice_reverts(contract):
    contract.observe()
    contract.pause()
    with pytest.raises(Exception, match="ALREADY_PAUSED"):
        contract.pause()


def test_unpause_without_pause_reverts(contract):
    contract.observe()
    with pytest.raises(Exception, match="NOT_PAUSED"):
        contract.unpause()


def test_bounds_are_set(contract):
    bounds = contract.get_bounds()
    assert bounds["interest_min"] == 0
    assert bounds["interest_max"] == 20000
    assert bounds["collateral_min"] == 100000
    assert bounds["collateral_max"] == 200000
    assert bounds["supply_min"] == -5000
    assert bounds["supply_max"] == 5000


def test_propose_without_observation_reverts(contract):
    contract.observe()
    with pytest.raises(Exception, match="NO_OBSERVATION"):
        contract.propose_policy(1, "set_interest_rate:2.5", 100)


def test_propose_with_invalid_direction_reverts(contract):
    contract.observe()
    # direction "make_it_rain" should fail parse
    with pytest.raises(Exception, match="INVALID_DIRECTION"):
        contract.propose_policy(1, "make_it_rain", 100)


def test_propose_with_out_of_bounds_reverts(contract):
    contract.observe()
    with pytest.raises(Exception, match="OUT_OF_BOUNDS"):
        contract.propose_policy(1, "set_interest_rate:50", 100)


def test_propose_with_low_bond_reverts(contract):
    contract.observe()
    # bond 50 < min_bond 100
    with pytest.raises(Exception, match="BOND_TOO_LOW"):
        contract.propose_policy(1, "set_interest_rate:2.5", 50)


def test_get_proposal_count_starts_at_zero(contract):
    assert contract.get_proposal_count() == 0


def test_get_history_empty(contract):
    history = contract.get_history(1, 10)
    assert history == []