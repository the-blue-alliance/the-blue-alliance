from backend.common.deferred.queues.rq_queue import RQTaskQueue


class FakeTaskQueue(RQTaskQueue):
    """
    A RQ-backed queue, but will run jobs inline
    instead of making a HTTP request callback
    """

    def jobs(self):
        return self._queue.jobs
