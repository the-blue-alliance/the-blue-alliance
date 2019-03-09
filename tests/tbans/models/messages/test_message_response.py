import unittest2

from tbans.models.messages.message_response import MessageResponse


class TestMessageResponse(unittest2.TestCase):

    def test_status_code(self):
        with self.assertRaises(ValueError):
            MessageResponse(status_code=None)

    def test_status_code_type(self):
        with self.assertRaises(TypeError):
            MessageResponse(status_code='abc')

    def test_content_type(self):
        with self.assertRaises(TypeError):
            MessageResponse(status_code=200, content=200)

    def test_init(self):
        _status_code = 404
        _content = 'Some content here'
        response = MessageResponse(status_code=_status_code, content=_content)
        self.assertEqual(response.status_code, _status_code)
        self.assertEqual(response.content, _content)

    def test_str(self):
        response = MessageResponse(status_code=400)
        self.assertEqual(str(response), 'MessageResponse(code=400 content=None)')

    def test_str_content(self):
        response = MessageResponse(status_code=400, content='Some content here')
        self.assertEqual(str(response), 'MessageResponse(code=400 content="Some content here")')
