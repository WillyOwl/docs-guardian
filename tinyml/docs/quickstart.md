# Quickstart

Predict house prices from the sample dataset in under ten lines.

```python
from tinyml import evaluate, fit_linear, load_csv, train_test_split

X, y = load_csv("data/housing.csv", target="price")
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

model = fit_linear(X_train, y_train)
rmse = evaluate(y_test, model.predict(X_test))
print(f"RMSE: {rmse:,.0f}")
```

`evaluate` returns the root mean squared error, in the same units as the target: here, dollars. Lower is better.

Next, the [Tutorial](tutorial.md) walks through each step.
