"""Linear regression."""

import numpy as np


class LinearModel:
    """A fitted linear model: `prediction = X @ coef + intercept`.

    Create one with `fit_linear` rather than directly.
    """

    def __init__(self, coef: np.ndarray, intercept: float) -> None:
        """Store fitted parameters.

        Args:
            coef: One coefficient per feature column.
            intercept: The constant term.
        """
        self.coef = coef
        self.intercept = intercept

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict a target value for every row of `X`.

        Args:
            X: Feature matrix with the same columns, in the same order, as the
                data the model was fitted on.

        Returns:
            A 1-D array with one prediction per row.
        """
        return np.asarray(X) @ self.coef + self.intercept


def fit_linear(X: np.ndarray, y: np.ndarray) -> LinearModel:
    """Fit ordinary least squares with an intercept.

    Args:
        X: Feature matrix, one row per sample.
        y: Target values, one per row of `X`.

    Returns:
        A `LinearModel` with `.coef`, `.intercept` and `.predict()`.
    """
    X = np.asarray(X, dtype=float)
    design = np.column_stack([X, np.ones(len(X))])
    solution, *_ = np.linalg.lstsq(design, np.asarray(y, dtype=float), rcond=None)
    return LinearModel(coef=solution[:-1], intercept=float(solution[-1]))
