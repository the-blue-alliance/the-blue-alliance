import abc


class CloudRunClient(abc.ABC):
    @abc.abstractmethod
    def start_job(
        self,
        job_name: str,
        args: list[str] = None,
        env: dict[str, str] = None,
    ) -> str: ...

    @abc.abstractmethod
    def get_job_status(self, job_name: str, execution_id: str) -> str | None: ...
