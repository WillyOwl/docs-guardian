# Tutorial

This page builds the Quickstart up one step at a time. Each code block continues from the one before it.

## 1. Load the data

`load_csv` reads a CSV with a header row and splits it into features and a target. Name the column you want to predict; every other column becomes a feature, in file order.

This tutorial uses the sample CSV that ships with tinyml; `housing_path()` gives its location. For your own data, pass your file's path instead.

```python
from tinyml import load_csv
from tinyml.datasets import housing_path

X, y = load_csv(housing_path(), target="price")
print(X.shape, y.shape)
```

`X` has one row per house and three columns: `size_sqft`, `bedrooms` and `age_years`. `y` holds the 40 prices.

## 2. Hold out a test set

A model always looks good on the data it was fitted on, so keep some rows aside to score it honestly.

```python
from tinyml import train_test_split

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, seed=0)
print(len(y_train), len(y_test))
```

With `test_size=0.2`, 8 of the 40 houses go to the test set. The split is shuffled, and the same `seed` always gives the same split.

## 3. Fit a model

`fit` fits ordinary least squares with an intercept and returns a `LinearModel`.

```python
from tinyml import fit

model = fit(X_train, y_train)
print(model.coef, model.intercept)
```

`model.coef` holds one number per feature: how much the predicted price moves when that feature goes up by one. Size should come out at roughly 120 dollars per square foot, and age should come out negative, since older houses sell for less.

## 4. Score it

`predict` returns one prediction per row, and `evaluate` compares predictions with the true values.

```python
from tinyml import evaluate

y_pred = model.predict(X_test)
print(f"RMSE: {evaluate(y_test, y_pred):,.0f}")
```

`evaluate` returns the root mean squared error (RMSE): a typical prediction is off by about this many dollars. Lower is better, and 0 would mean every prediction is exact.

## 5. Predict a new house

`predict` takes the same columns, in the same order, as the training data.

```python
import numpy as np

new_house = np.array([[1800, 3, 10]])  # size_sqft, bedrooms, age_years
print(f"Predicted price: {model.predict(new_house)[0]:,.0f}")
```
