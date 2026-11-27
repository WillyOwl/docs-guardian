# tinyml

tinyml is a tiny linear-regression library: load a CSV, split it, fit a model, and score it, in five functions.

```bash
pip install "tinyml @ git+https://github.com/WillyOwl/docs-guardian#subdirectory=tinyml"
```

tinyml is not published on PyPI; it installs straight from this repository.

- New here? Start with the [Quickstart](quickstart.md).
- Want to see each step explained? Read the [Tutorial](tutorial.md), or follow the same flow in the [notebook](notebooks/walkthrough.ipynb).
- Looking for a specific function? See the [API reference](api.md).

The examples use a small sample dataset that ships with tinyml: 40 houses with their size, number of bedrooms, age and sale price. Load it with `tinyml.datasets.housing()`, or [view the CSV](https://github.com/WillyOwl/docs-guardian/blob/main/tinyml/src/tinyml/_data/housing.csv).

Found a problem? Report it on Github, or read the [roadmap](https://willyowl.github.io/docs-guardian/missing/).
