import pytest

from tools import check_vendor_availability, get_maintenance_history, lookup_hoa_policy


def test_policy_lookup():
    result = lookup_hoa_policy.invoke({"issue_type": "plumbing"})
    assert "Responsibility:" in result


def test_history_lookup():
    result = get_maintenance_history.invoke({"unit_number": "B204"})
    assert isinstance(result, str)


def test_vendor_failure_then_success():
    with pytest.raises(ConnectionError):
        check_vendor_availability.invoke({
            "issue_type": "garage",
            "attempt": 0,
            "simulate_failure": True,
        })

    result = check_vendor_availability.invoke({
        "issue_type": "garage",
        "attempt": 2,
        "simulate_failure": True,
    })
    assert "available" in result.lower()
