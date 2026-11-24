"""Scoring predictions."""

import numpy as np


def evaluate(y: np.ndarray, y_pred: np.ndarray) -> float:
    """Score predictions with root mean squared error (RMSE).

    Lower is better; 0 means every prediction is exact. The result is in the
    same units as `y`.

    Args:
        y: True target values.
        y_pred: Predicted values, one per entry of `y`.

    Returns:
        The RMSE as a float.
    """
    y, y_pred = np.asarray(y, dtype=float), np.asarray(y_pred, dtype=float)
    return float(np.sqrt(np.mean((y - y_pred) ** 2)))
