"""Loading and splitting tabular data."""

import csv
from pathlib import Path

import numpy as np


def load_csv(path: str | Path, target: str) -> tuple[np.ndarray, np.ndarray]:
    """Load a numeric CSV file into features and a target.

    Args:
        path: Path to a CSV file with a header row. Every column must be numeric.
        target: Name of the column to predict.

    Returns:
        A tuple `(X, y)`: `X` is a 2-D array of every column except `target`,
        in file order, and `y` is a 1-D array of the `target` column.

    Raises:
        KeyError: If `target` is not a column in the file.
    """
    with open(path, newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = [[float(value) for value in row] for row in reader if row]
    if target not in header:
        raise KeyError(f"column {target!r} not in {header}")
    data = np.array(rows)
    t = header.index(target)
    features = [i for i in range(len(header)) if i != t]
    return data[:, features], data[:, t]


def train_test_split(
    X: np.ndarray, y: np.ndarray, test_size: float = 0.2, seed: int = 0
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Shuffle rows and split them into a training set and a test set.

    Args:
        X: Feature matrix, one row per sample.
        y: Target values, one per row of `X`.
        test_size: Fraction of rows to hold out for testing, between 0 and 1.
            The test set always gets at least one row.
        seed: Random seed, so the same inputs always give the same split.

    Returns:
        A tuple `(X_train, X_test, y_train, y_test)`.

    Raises:
        ValueError: If `test_size` is not strictly between 0 and 1, or if the
            split would leave no rows for training.
    """
    if not 0 < test_size < 1:
        raise ValueError(f"test_size must be between 0 and 1, got {test_size}")
    order = np.random.default_rng(seed).permutation(len(y))
    n_test = max(1, round(len(y) * test_size))
    if n_test >= len(y):
        raise ValueError(
            f"test_size={test_size} puts {n_test} of {len(y)} rows in the test set,"
            " leaving no training rows"
        )
    test, train = order[:n_test], order[n_test:]
    return X[train], X[test], y[train], y[test]
