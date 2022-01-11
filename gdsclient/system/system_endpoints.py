from typing import Optional

from ..query_runner.query_runner import QueryResult, QueryRunner


class SystemEndpoints:
    def __init__(self, query_runner: QueryRunner, namespace: str):
        self._query_runner = query_runner
        self._namespace = namespace

    def listProgress(self, job_id: Optional[str] = None) -> QueryResult:
        self._namespace += ".listProgress"

        if job_id:
            query = f"CALL {self._namespace}($job_id)"
            params = {"job_id": job_id}
        else:
            query = f"CALL {self._namespace}()"
            params = {}

        return self._query_runner.run_query(query, params)
