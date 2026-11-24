"""Scoring predictions."""

import numpy as np

from tinyml._validation import as_target, require_same_count


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
    y, y_pred = as_target(y, "y"), as_target(y_pred, "y_pred")
    require_same_count(y, "y", "values", y_pred, "y_pred")
    return float(np.sqrt(np.mean((y - y_pred) ** 2)))
