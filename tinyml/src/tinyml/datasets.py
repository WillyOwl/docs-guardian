"""Sample data that ships with tinyml, so examples run anywhere with no download."""

from importlib.resources import files
from pathlib import Path

import numpy as np

from tinyml.data import load_csv


def housing_path() -> Path:
    """Locate the bundled housing CSV.

    The file has a header row and 40 houses with four numeric columns:
    `size_sqft`, `bedrooms`, `age_years` and `price` (sale price in dollars).

    Returns:
        The path to `housing.csv` inside the installed tinyml package.
    """
    return Path(str(files("tinyml").joinpath("_data", "housing.csv")))


def housing() -> tuple[np.ndarray, np.ndarray]:
    """Load the bundled housing dataset, ready to fit.

    Returns:
        A tuple `(X, y)`: `X` has 40 rows and the columns `size_sqft`,
        `bedrooms` and `age_years`; `y` holds the 40 sale prices.
    """
    return load_csv(housing_path(), target="price")
