from onboard.services.ranking import cosine_to_unit


def test_cosine_to_unit_mapping():
    assert cosine_to_unit(-1.0) == 0.0
    assert cosine_to_unit(0.0) == 0.5
    assert cosine_to_unit(1.0) == 1.0
