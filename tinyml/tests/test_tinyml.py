import subprocess
import sys

import numpy as np
import pytest

from tinyml import LinearModel, evaluate, fit_linear, load_csv, train_test_split
from tinyml.datasets import housing, housing_path


def test_load_csv_splits_target_from_features(tmp_path):
    path = tmp_path / "d.csv"
    path.write_text("a,target,b\n1,10,2\n3,30,4\n")
    X, y = load_csv(path, target="target")
    assert X.tolist() == [[1, 2], [3, 4]]
    assert y.tolist() == [10, 30]


def test_housing_dataset_loads_from_any_working_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # an empty folder, like a reader's fresh project
    X, y = housing()
    assert (X.shape, y.shape) == ((40, 3), (40,))
    assert X[0].tolist() == [832, 1, 51]  # size_sqft, bedrooms, age_years
    assert y[0] == 88200


def test_datasets_is_reachable_from_the_package():
    # A fresh interpreter: this test module's own imports would load the submodule.
    code = "import tinyml; X, y = tinyml.datasets.housing(); print(len(X))"  # as on the home page
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "40"


def test_housing_path_is_a_csv_that_load_csv_reads(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    X, y = load_csv(housing_path(), target="price")
    assert (X.shape, y.shape) == ((40, 3), (40,))


def test_load_csv_unknown_target(tmp_path):
    path = tmp_path / "d.csv"
    path.write_text("a,b\n1,2\n")
    with pytest.raises(KeyError):
        load_csv(path, target="price")


def test_train_test_split_sizes_and_determinism():
    X, y = np.arange(20).reshape(10, 2), np.arange(10)
    first = train_test_split(X, y, test_size=0.3, seed=1)
    X_train, X_test, y_train, y_test = first
    assert (len(X_train), len(X_test)) == (7, 3)
    assert sorted([*y_train, *y_test]) == list(range(10))
    second = train_test_split(X, y, test_size=0.3, seed=1)
    assert all(np.array_equal(a, b) for a, b in zip(first, second, strict=True))


@pytest.mark.parametrize("bad", [0, 1, -0.5, 1.5])
def test_train_test_split_rejects_bad_size(bad):
    with pytest.raises(ValueError):
        train_test_split(np.zeros((4, 1)), np.zeros(4), test_size=bad)


@pytest.mark.parametrize(
    ("n_rows", "test_size"),
    [
        (2, 0.8),  # 0.8 of 2 rounds to 2 test rows, leaving none to train on
        (1, 0.5),  # one row cannot be both trained on and tested
    ],
)
def test_train_test_split_rejects_split_with_no_training_rows(n_rows, test_size):
    X, y = np.zeros((n_rows, 1)), np.zeros(n_rows)
    with pytest.raises(ValueError, match="training"):
        train_test_split(X, y, test_size=test_size)


# The sample rules every function taking (X, y) enforces, one case per rule.
BAD_SAMPLES = [
    pytest.param(np.zeros(3), np.zeros(3), "X must be 2-D", id="X-1d"),  # 1-D X is ambiguous
    pytest.param(np.zeros((3, 1)), np.zeros((3, 2)), "y must be 1-D or a single", id="y-2col"),
    pytest.param(np.zeros((5, 1)), np.zeros(4), "5 rows but y has 4", id="count-mismatch"),
    pytest.param(np.zeros((0, 1)), np.zeros(0), "empty", id="empty"),
]


@pytest.mark.parametrize("fn", [fit_linear, train_test_split], ids=lambda f: f.__name__)
@pytest.mark.parametrize(("X", "y", "reason"), BAD_SAMPLES)
def test_functions_taking_samples_reject_bad_input(fn, X, y, reason):
    with pytest.raises(ValueError, match=reason):
        fn(X, y)


def test_train_test_split_returns_a_column_target_as_1d():
    X, y = np.arange(10.0).reshape(5, 2), np.arange(5.0).reshape(5, 1)
    _, _, y_train, y_test = train_test_split(X, y, test_size=0.4)
    assert (y_train.ndim, y_test.ndim) == (1, 1)
    assert sorted([*y_train, *y_test]) == [0, 1, 2, 3, 4]


def test_fit_linear_recovers_exact_relation():
    X = np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0], [2.0, 3.0]])
    y = 3 * X[:, 0] - 2 * X[:, 1] + 5
    model = fit_linear(X, y)
    assert isinstance(model, LinearModel)
    assert np.allclose(model.coef, [3, -2])
    assert model.intercept == pytest.approx(5)
    assert np.allclose(model.predict(X), y)


def test_fit_linear_accepts_target_as_a_single_column():
    X = np.array([[1.0], [2.0], [3.0]])
    model = fit_linear(X, np.array([[7.0], [9.0], [11.0]]))  # y = 2x + 5
    assert np.allclose(model.coef, [2])
    assert model.intercept == pytest.approx(5)
    assert model.predict(X).shape == (3,)


@pytest.mark.parametrize(
    ("X", "reason"),
    [
        ([1.0, 2.0], "X must be 2-D"),  # one sample with 2 features, or 2 samples? ambiguous
        ([[1.0, 2.0, 3.0]], "3 columns but the model was fitted on 2"),
        (np.zeros((0, 2)), "empty"),
    ],
)
def test_predict_rejects_bad_input(X, reason):
    model = LinearModel(coef=np.array([1.0, 2.0]), intercept=0.0)
    with pytest.raises(ValueError, match=reason):
        model.predict(X)


def test_evaluate_is_rmse():
    assert evaluate([1, 2, 3], [1, 2, 3]) == 0
    assert evaluate([0, 0], [3, 4]) == pytest.approx(np.sqrt(12.5))


def test_evaluate_accepts_predictions_as_a_single_column():
    assert evaluate([1, 2, 3], [[1], [2], [3]]) == 0


@pytest.mark.parametrize(
    ("y", "y_pred", "reason"),
    [
        ([0, 2], [0], "2 values but y_pred has 1"),  # a missing prediction must not broadcast
        ([1, 2], [[1, 2], [1, 2]], "single column"),  # a matrix is not one prediction per sample
        ([], [], "empty"),  # nothing to score
    ],
)
def test_evaluate_rejects_mismatched_or_empty_input(y, y_pred, reason):
    with pytest.raises(ValueError, match=reason):
        evaluate(y, y_pred)
