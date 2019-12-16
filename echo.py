# -*- coding: utf-8 -*-
# @Time 2019-10-30 18:07

from flask import Flask
from flask import Flask, jsonify, request
app = Flask(__name__)

ALL_METHODS = ["GET", "HEAD", "POST", "PUT", "DELETE", "OPTIONS"]


@app.route("/", defaults={"path": ""}, methods=ALL_METHODS)
@app.route("/<path:path>", methods=ALL_METHODS)
def index(path):
    data = {
        "path": request.path,
        "method": request.method,
        "headers": list(request.headers.items()),
        "form": list(request.form.items()),
        "args": list(request.args.items()),
        "remote": {
            "address": request.environ.get("REMOTE_ADDR", "???"),
            "port": request.environ.get("REMOTE_PORT", "???"),
        },
        "content-type": request.content_type,
        "files": [(f[0], f[1].filename) for f in request.files.items()],
        "json": request.json,
        "raw-data": str(request.data),
    }
    return jsonify(data)


if __name__ == '__main__':
    # db.drop_all()
    app.run(host='0.0.0.0', port=5000, debug=True)