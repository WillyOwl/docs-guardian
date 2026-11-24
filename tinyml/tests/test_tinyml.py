import numpy as np
import pytest

from tinyml import LinearModel, evaluate, fit_linear, load_csv, train_test_split


def test_load_csv_splits_target_from_features(tmp_path):
    path = tmp_path / "d.csv"
    path.write_text("a,target,b\n1,10,2\n3,30,4\n")
    X, y = load_csv(path, target="target")
    assert X.tolist() == [[1, 2], [3, 4]]
    assert y.tolist() == [10, 30]


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


def test_fit_linear_recovers_exact_relation():
    X = np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0], [2.0, 3.0]])
    y = 3 * X[:, 0] - 2 * X[:, 1] + 5
    model = fit_linear(X, y)
    assert isinstance(model, LinearModel)
    assert np.allclose(model.coef, [3, -2])
    assert model.intercept == pytest.approx(5)
    assert np.allclose(model.predict(X), y)


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
