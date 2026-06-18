import numpy as np

from huff_curves_br.metrics import fitness_metrics, kling_gupta_efficiency


def test_kge_and_fitness_are_perfect_for_identical_curves():
    curve = np.linspace(0.1, 1.0, 10)

    assert kling_gupta_efficiency(curve, curve) == 1.0
    metrics = fitness_metrics(curve, curve)
    assert metrics.kge == 1.0
    assert metrics.rmse == 0.0
    assert metrics.mae == 0.0
    assert metrics.d_max == 0.0
    assert metrics.n_valid == 10
