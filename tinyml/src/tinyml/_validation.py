"""Input checks shared by every public function that takes features or targets.

The rules, applied the same way everywhere:

- features (`X`) are 2-D: one row per sample, one column per feature;
- targets (`y`, `y_pred`) are 1-D or a single column, and come back 1-D;
- paired inputs hold the same number of samples;
- inputs are not empty.
"""

import numpy as np


def as_features(X: np.ndarray) -> np.ndarray:
    """Return features as a 2-D float array.

    Args:
        X: Feature matrix, one row per sample.

    Returns:
        `X` as a 2-D float array.

    Raises:
        ValueError: If `X` is not 2-D or has no rows.
    """
    X = np.asarray(X, dtype=float)
    if X.ndim != 2:
        raise ValueError(
            f"X must be 2-D (one row per sample), got shape {X.shape};"
            " use X.reshape(-1, 1) for a single feature"
        )
    _require_values(X, "X")
    return X


def as_target(values: np.ndarray, name: str) -> np.ndarray:
    """Return a target as a 1-D float array.

    Args:
        values: A 1-D array or a single column.
        name: The argument's name, for error messages.

    Returns:
        The values as a 1-D float array.

    Raises:
        ValueError: If `values` has any other shape or is empty.
    """
    values = np.asarray(values, dtype=float)
    if values.ndim == 2 and values.shape[1] == 1:
        values = values[:, 0]
    if values.ndim != 1:
        raise ValueError(f"{name} must be 1-D or a single column, got shape {values.shape}")
    _require_values(values, name)
    return values


def as_samples(X: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return features and targets, checked to describe the same samples.

    Args:
        X: Feature matrix, one row per sample.
        y: Target values, one per row of `X`.

    Returns:
        `(X, y)` as a 2-D and a 1-D float array.

    Raises:
        ValueError: If either breaks a rule above, or if their sample counts differ.
    """
    X, y = as_features(X), as_target(y, "y")
    require_same_count(X, "X", "rows", y, "y")
    return X, y


def require_same_count(a: np.ndarray, a_name: str, unit: str, b: np.ndarray, b_name: str) -> None:
    """Check that two inputs hold one entry per sample each.

    Args:
        a: The first input; its length is its sample count.
        a_name: Its argument name, for the error message.
        unit: What one entry of `a` is called ("rows", "values").
        b: The second input.
        b_name: Its argument name.

    Raises:
        ValueError: If their lengths differ.
    """
    if len(a) != len(b):
        raise ValueError(f"{a_name} has {len(a)} {unit} but {b_name} has {len(b)}")


def _require_values(values: np.ndarray, name: str) -> None:
    if len(values) == 0:
        raise ValueError(f"{name} is empty; there are no samples")
