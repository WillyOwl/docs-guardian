"""Linear regression."""

import numpy as np

from tinyml._validation import as_features, as_samples


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
            X: 2-D feature matrix with the same columns, in the same order, as
                the data the model was fitted on. For a single sample, pass one
                row: `[[...]]`.

        Returns:
            A 1-D array with one prediction per row.

        Raises:
            ValueError: If `X` is not 2-D, has a different number of columns
                than the model was fitted on, or is empty.
        """
        X = as_features(X)
        if X.shape[1] != len(self.coef):
            raise ValueError(
                f"X has {X.shape[1]} columns but the model was fitted on {len(self.coef)}"
            )
        return X @ self.coef + self.intercept


def fit_linear(X: np.ndarray, y: np.ndarray) -> LinearModel:
    """Fit ordinary least squares with an intercept.

    Args:
        X: 2-D feature matrix, one row per sample.
        y: Target values, one per row of `X`, 1-D or a single column.

    Returns:
        A `LinearModel` with `.coef`, `.intercept` and `.predict()`.

    Raises:
        ValueError: If `X` is not 2-D, if `y` is not 1-D or a single column,
            or if their sample counts differ or they are empty.
    """
    X, y = as_samples(X, y)
    design = np.column_stack([X, np.ones(len(X))])
    solution, *_ = np.linalg.lstsq(design, y, rcond=None)
    return LinearModel(coef=solution[:-1], intercept=float(solution[-1]))

# A change that alters no API.
