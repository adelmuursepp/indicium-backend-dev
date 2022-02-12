from http import HTTPStatus


class InvalidUsage(Exception):
    status_code = HTTPStatus.BAD_REQUEST

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def message(self):
        return self.message

    def to_dict(self):
        rv = dict(self.payload or ())
        rv["message"] = self.message
        return rv
