import numpy as np
import pytest

from edd_world.adapter import to_record
from edd_world.cases import sample_case


@pytest.fixture(scope="session")
def world_cases():
    rng = np.random.default_rng(7)
    return [sample_case(rng, f"t{i:03d}", 1) for i in range(240)]


@pytest.fixture(scope="session")
def records(world_cases):
    return [to_record(c) for c in world_cases]
