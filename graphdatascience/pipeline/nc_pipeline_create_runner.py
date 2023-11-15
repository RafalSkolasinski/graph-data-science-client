from typing import Any, Tuple

from pandas import Series

from ..error.illegal_attr_checker import IllegalAttrChecker
from ..error.uncallable_namespace import UncallableNamespace
from .nc_training_pipeline import NCTrainingPipeline


class NCPipelineCreateRunner(UncallableNamespace, IllegalAttrChecker):
    def create(self, name: str) -> Tuple[NCTrainingPipeline, "Series[Any]"]:
        self._namespace += ".create"

        params = {"name": name}
        result = self._query_runner.call_procedure(endpoint=self._namespace, body="$name", params=params).squeeze()

        return NCTrainingPipeline(name, self._query_runner, self._server_version), result
