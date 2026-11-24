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
