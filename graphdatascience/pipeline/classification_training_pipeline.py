from abc import ABC
from typing import Any

from pandas import Series

from ..server_version.server_version import ServerVersion
from .training_pipeline import MODEL_TYPE, TrainingPipeline


class ClassificationTrainingPipeline(TrainingPipeline[MODEL_TYPE], ABC):
    def addLogisticRegression(self, **config: Any) -> "Series[Any]":
        """
        Add a logistic regression model candidate to the pipeline.

        Args:
            **config: The configuration for the logistic regression model.

        Returns:
            The result of the query.
        """
        params = {"pipeline_name": self.name(), "config": self._expand_ranges(config)}

        return self._query_runner.call_procedure(
            endpoint=f"{self._endpoint_prefix()}addLogisticRegression",
            body="$pipeline_name, $config",
            params=params,
        ).squeeze()  # type: ignore

    def addRandomForest(self, **config: Any) -> "Series[Any]":
        """
        Add a random forest model candidate to the pipeline.

        Args:
            **config: The configuration for the random forest model.

        Returns:
            The result of the query.

        """
        endpoint_prefix = self._endpoint_prefix()
        if self._server_version < ServerVersion(2, 4, 0):
            endpoint_prefix = self._endpoint_prefix().replace("beta", "alpha")
        params = {"pipeline_name": self.name(), "config": self._expand_ranges(config)}

        return self._query_runner.call_procedure(
            endpoint=f"{endpoint_prefix}addRandomForest", body="$pipeline_name, $config", params=params
        ).squeeze()  # type: ignore

    def addMLP(self, **config: Any) -> "Series[Any]":
        """
        Add a multi-layer perceptron model candidate to the pipeline.

        Args:
            **config: The configuration for the multi-layer perceptron model.

        Returns:
            The result of the query.

        """
        endpoint_prefix = self._endpoint_prefix().replace("beta", "alpha")
        params = {"pipeline_name": self.name(), "config": self._expand_ranges(config)}

        return self._query_runner.call_procedure(
            endpoint=f"{endpoint_prefix}addMLP", body="$pipeline_name, $config", params=params
        ).squeeze()  # type: ignore
