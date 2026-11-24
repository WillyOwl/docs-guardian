"""tinyml: load a CSV, split it, fit a linear model, and score it."""

from tinyml.data import load_csv, train_test_split
from tinyml.metrics import evaluate
from tinyml.models import LinearModel, fit_linear

__all__ = ["LinearModel", "evaluate", "fit_linear", "load_csv", "train_test_split"]
