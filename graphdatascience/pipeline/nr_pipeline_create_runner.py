from typing import Any, Tuple

from pandas import Series

from ..error.illegal_attr_checker import IllegalAttrChecker
from ..error.uncallable_namespace import UncallableNamespace
from .nr_training_pipeline import NRTrainingPipeline


class NRPipelineCreateRunner(UncallableNamespace, IllegalAttrChecker):
    def create(self, name: str) -> Tuple[NRTrainingPipeline, "Series[Any]"]:
        self._namespace += ".create"

        params = {"name": name}
        result = self._query_runner.call_procedure(endpoint=self._namespace, body="$name", params=params).squeeze()

        return NRTrainingPipeline(name, self._query_runner, self._server_version), result
