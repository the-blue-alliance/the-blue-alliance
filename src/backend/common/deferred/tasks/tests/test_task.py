from backend.common.deferred.tasks.task import Task


def test_init():
    task = Task(print, "a", b="c")
    assert task.obj == print
    assert task.args == ("a",)
    assert task.kwargs == {"b": "c"}


def test_serialize():
    task = Task(print, "a", b="c")
    b = task.serialize()
    assert b is not None
    assert type(b) is bytes
