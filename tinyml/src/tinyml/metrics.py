"""Scoring predictions."""

import numpy as np


def evaluate(y: np.ndarray, y_pred: np.ndarray) -> float:
    """Score predictions with root mean squared error (RMSE).

    Lower is better; 0 means every prediction is exact. The result is in the
    same units as `y`.

    Args:
        y: True target values, 1-D or a single column.
        y_pred: Predicted values, one per entry of `y`, 1-D or a single column.

    Returns:
        The RMSE as a float.

    Raises:
        ValueError: If either input has any other shape, if they hold different
            numbers of values, or if they are empty.
    """
    y, y_pred = _as_vector(y, "y"), _as_vector(y_pred, "y_pred")
    if len(y) != len(y_pred):
        raise ValueError(f"y has {len(y)} values but y_pred has {len(y_pred)}")
    if len(y) == 0:
        raise ValueError("y and y_pred are empty; there is nothing to score")
    return float(np.sqrt(np.mean((y - y_pred) ** 2)))


def _as_vector(values: np.ndarray, name: str) -> np.ndarray:
    """Return `values` as 1-D, accepting a single column, so entries pair up one to one."""
    values = np.asarray(values, dtype=float)
    if values.ndim == 2 and values.shape[1] == 1:
        values = values[:, 0]
    if values.ndim != 1:
        raise ValueError(f"{name} must be 1-D or a single column, got shape {values.shape}")
    return values
