from flask import Flask, jsonify, request
from helpers import check_authenticated
from http import HTTPStatus
from InvalidUsage import InvalidUsage
from auth_api import handle_auth_request

import firebase
import requests

app = Flask(__name__)


@app.route("/api", methods=["GET"])
@check_authenticated
def api():
    return request.user


@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    return error.message, error.status_code


if __name__ == "__main__":
    app.run(debug=True)
