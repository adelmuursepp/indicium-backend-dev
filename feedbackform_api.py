from helpers import check_authenticated
from http import HTTPStatus
from flask import Blueprint, jsonify, request
from firebase_admin import auth, firestore
from firebase_admin.exceptions import FirebaseError
from error_messages import USER_WITH_UID_NOT_FOUND, INVALID_UID

import firebase

feedbackform_api = Blueprint("feedbackform_api", __name__)


@feedbackform_api.route("/api/feedbackform", methods=["POST"])
@check_authenticated
def add_feedbackform_results():
    try:
        request_json = request.json
        uid = request.user["uid"]
        results = request_json["scores"]
        for i in results:
            if i == "0":
                return (
                    "Please fill out the all questions in the form",
                    HTTPStatus.BAD_REQUEST,
                )
        results = [int(x) for x in results]
        firebase.users_collection_ref.document(uid).update({"scores": results})
        return "Success", HTTPStatus.OK

    except ValueError:
        return INVALID_UID.format(uid), HTTPStatus.BAD_REQUEST
    except auth.UserNotFoundError:
        return USER_WITH_UID_NOT_FOUND.format(uid), HTTPStatus.NOT_FOUND
    except FirebaseError as e:
        return e.cause, e.code
