from backend.common.storage.clients.in_memory_client import InMemoryClient


def test_init():
    client = InMemoryClient()
    assert client.data == {}


def test_write():
    file_name = "some_file.json"
    file_content = "some_content"

    client = InMemoryClient()
    client.write(file_name, file_content)

    assert client.data == {file_name: file_content}


def test_read_none():
    file_name = "some_file.json"

    client = InMemoryClient()
    assert client.read(file_name) is None


def test_read():
    file_name = "some_file.json"
    file_content = "some_content"

    client = InMemoryClient()
    assert client.read(file_name) is None
    client.write(file_name, file_content)
    assert client.read(file_name) == file_content


def test_get_files():
    file_name = "some_file.json"
    file_content = "some_content"

    client = InMemoryClient()
    assert client.get_files() == []
    client.write(file_name, file_content)
    assert client.get_files() == ["some_file.json"]


def test_get_files_prefix():
    file_name = "some_file.json"
    file_content = "some_content"

    client = InMemoryClient()
    assert client.get_files() == []
    client.write(file_name, file_content)
    assert client.get_files("foo") == []
    assert client.get_files("some") == ["some_file.json"]
