from flask import Flask
from backend.api.handlers.error import handle_404
from backend.api.handlers.root import root
from backend.common.middleware import install_middleware


app = Flask(__name__)
install_middleware(app)
app.config["JSONIFY_PRETTYPRINT_REGULAR"] = True

app.add_url_rule("/api/v3/<path:path>", view_func=root)
app.register_error_handler(404, handle_404)
