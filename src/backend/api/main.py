from flask import Flask
from backend.api.handlers.root import root
from backend.common.middleware import install_middleware
from backend.common.profiler import send_request_context_traces


app = Flask(__name__)
install_middleware(app)

app.add_url_rule("/api/<path:path>", view_func=root)


@app.teardown_request
def teardown_request(exception):
    send_request_context_traces()
