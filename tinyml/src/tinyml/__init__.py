"""tinyml: load a CSV, split it, fit a linear model, and score it."""

# Re-exported so `tinyml.datasets.housing()` works after a plain `import tinyml`.
from tinyml import datasets as datasets
from tinyml.data import load_csv, train_test_split
from tinyml.metrics import evaluate
from tinyml.models import LinearModel, fit

__all__ = ["LinearModel", "evaluate", "fit", "load_csv", "train_test_split"]
