import math

from onboard.services.interest_map import decay_weight


def test_decay_half_life_exact():
    half = 10.0
    assert math.isclose(decay_weight(0, half), 1.0, rel_tol=1e-6)
    assert math.isclose(decay_weight(half, half), 0.5, rel_tol=1e-6)
    assert math.isclose(decay_weight(2 * half, half), 0.25, rel_tol=1e-6)
