######################################################################################
# Copyright (c) 2023 Orange. All rights reserved.                                    #
# This software is distributed under the BSD 3-Clause-clear License, the text of     #
# which is available at https://spdx.org/licenses/BSD-3-Clause-Clear.html or         #
# see the "LICENSE.md" file for more details.                                        #
######################################################################################
"""Tests for checking the output types of predictors"""
import os
import unittest

import pandas as pd
from numpy.testing import assert_array_equal
from sklearn import datasets
from sklearn.utils.validation import column_or_1d

from khiops.sklearn.estimators import KhiopsClassifier, KhiopsRegressor

# Disable PEP8 variable names because of scikit-learn X,y conventions
# To capture invalid-names other than X,y run:
#   pylint --disable=all --enable=invalid-names estimators.py
# pylint: disable=invalid-name


def create_iris():
    """Returns a mono table iris dataset"""
    X_iris_array, y_iris_array = datasets.load_iris(return_X_y=True)
    X_iris_df = pd.DataFrame(
        X_iris_array, columns=["SepalLenght", "SepalWidth", "PetalLength", "PetalWidth"]
    )
    y_iris_series = pd.Series(y_iris_array, name="Class")
    return X_iris_df, y_iris_series


def create_iris_mt():
    """Returns a multitable table iris dataset"""
    X_iris_df, y_iris_series = create_iris()
    X_iris_df["Id"] = X_iris_df.index
    X_iris_sec_df = X_iris_df.melt(
        id_vars=["Id"], var_name="Measurement", value_name="Value"
    )
    X_iris_df = X_iris_df.drop(
        ["SepalLenght", "SepalWidth", "PetalLength", "PetalWidth"], axis=1
    )
    return X_iris_df, X_iris_sec_df, y_iris_series


class KhiopsSklearnOutputTypes(unittest.TestCase):
    """Tests for checking the output types of predictors"""

    def setUp(self):
        if "UNITTEST_ONLY_SHORT_TESTS" in os.environ:
            if os.environ["UNITTEST_ONLY_SHORT_TESTS"].lower() == "true":
                self.skipTest("Skipping long test")

    def test_classifier_output_types(self):
        """Test the KhiopsClassifier output types and classes of predict* methods"""
        X, y = create_iris()
        X_mt, X_sec_mt, _ = create_iris_mt()

        fixtures = {
            "ys": {
                "int": y,
                "int binary": y.replace({0: 0, 1: 0, 2: 1}),
                "string": y.replace({0: "se", 1: "vi", 2: "ve"}),
                "string binary": y.replace({0: "vi_or_se", 1: "vi_or_se", 2: "ve"}),
                "int as string": y.replace({0: "8", 1: "9", 2: "10"}),
                "int as string binary": y.replace({0: "89", 1: "89", 2: "10"}),
                "cat int": y.astype("category"),
                "cat string": y.replace({0: "se", 1: "vi", 2: "ve"}).astype("category"),
            },
            "y_type_check": {
                "int": pd.api.types.is_integer_dtype,
                "int binary": pd.api.types.is_integer_dtype,
                "string": pd.api.types.is_string_dtype,
                "string binary": pd.api.types.is_string_dtype,
                "int as string": pd.api.types.is_string_dtype,
                "int as string binary": pd.api.types.is_string_dtype,
                "cat int": pd.api.types.is_integer_dtype,
                "cat string": pd.api.types.is_string_dtype,
            },
            "expected_classes": {
                "int": column_or_1d([0, 1, 2]),
                "int binary": column_or_1d([0, 1]),
                "string": column_or_1d(["se", "ve", "vi"]),
                "string binary": column_or_1d(["ve", "vi_or_se"]),
                "int as string": column_or_1d(["10", "8", "9"]),
                "int as string binary": column_or_1d(["10", "89"]),
                "cat int": column_or_1d([0, 1, 2]),
                "cat string": column_or_1d(["se", "ve", "vi"]),
            },
            "Xs": {
                "mono": X,
                "multi": {
                    "main_table": "iris_main",
                    "tables": {
                        "iris_main": (X_mt, "Id"),
                        "iris_sec": (X_sec_mt, "Id"),
                    },
                },
            },
        }

        # Test for each fixture configuration
        for y_type, y in fixtures["ys"].items():
            y_type_check = fixtures["y_type_check"][y_type]
            expected_classes = fixtures["expected_classes"][y_type]
            for dataset_type, X in fixtures["Xs"].items():
                with self.subTest(
                    y_type=y_type,
                    dataset_type=dataset_type,
                    estimator=KhiopsClassifier.__name__,
                ):
                    # Train the classifier
                    khc = KhiopsClassifier(n_trees=0)
                    khc.fit(X, y)

                    # Check the expected classes
                    assert_array_equal(khc.classes_, expected_classes)

                    # Check the return type of predict
                    y_pred = khc.predict(X)
                    self.assertTrue(
                        y_type_check(y_pred),
                        f"Invalid predict return type {y_pred.dtype}.",
                    )

                    # Check the dimensions of predict_proba
                    y_probas = khc.predict_proba(X)
                    self.assertEqual(len(y_probas.shape), 2)
                    self.assertEqual(y_probas.shape[1], len(khc.classes_))

    def test_regression_output_types(self):
        """Test the KhiopsRegressor output types of the predict method"""
        X, y = create_iris()
        X_mt, X_sec_mt, _ = create_iris_mt()

        fixtures = {
            "ys": {"int": y, "float": y.astype(float)},
            "Xs": {
                "mono": X,
                "multi": {
                    "main_table": "iris_main",
                    "tables": {
                        "iris_main": (X_mt, "Id"),
                        "iris_sec": (X_sec_mt, "Id"),
                    },
                },
            },
        }

        for y_type, y in fixtures["ys"].items():
            for dataset_type, X in fixtures["Xs"].items():
                with self.subTest(
                    y_type=y_type,
                    dataset_type=dataset_type,
                    estimator=KhiopsClassifier.__name__,
                ):
                    # Train the classifier
                    khr = KhiopsRegressor()
                    khr.fit(X, y)

                    # Check the return type of predict
                    y_pred = khr.predict(X)
                    self.assertTrue(
                        pd.api.types.is_float_dtype(y_pred),
                        f"Invalid predict return type {y_pred.dtype}.",
                    )
