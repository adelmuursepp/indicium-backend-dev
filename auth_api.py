from flask import Blueprint, request, make_response
from helpers import check_authenticated
from http import HTTPStatus

import datetime
import firebase
import json
import requests
import InvalidUsage

auth_api = Blueprint("auth_api", __name__)


@auth_api.route("/api/sign_up", methods=["POST"])
def sign_up():
    """
    Request JSON parameters:
    - email: str
    - password: str
    - student: bool
    - avatar: str
    """
    request_json = request.json
    request_json["emailVerified"] = False
    response_data, response_code = handle_auth_request(
        firebase.firebase_accounts_api(method="signUp"), request_json
    )

    if response_code == HTTPStatus.OK:
        verification_request = {
            "requestType": "VERIFY_EMAIL",
            "idToken": response_data["idToken"],
        }
        verify_response_data, verify_response_code = handle_auth_request(
            firebase.firebase_accounts_api(method="sendOobCode"), verification_request
        )

        if verify_response_code == HTTPStatus.OK:
            uid = response_data["localId"]
            firebase.create_user_doc(
                uid, request_json["student"], request_json["avatar"]
            )

        return create_response_with_token(response_data, response_code)
    return response_data, response_code


@auth_api.route("/api/sign_in", methods=["POST"])
def sign_in():
    """
    Request JSON parameters:
    - email: str
    - password: str
    """
    request_json = request.json
    request_json["returnSecureToken"] = True
    response_data, response_code = handle_auth_request(
        firebase.firebase_accounts_api(method="signInWithPassword"), request.json
    )

    if response_code == HTTPStatus.OK:
        user_info = firebase.get_user_info_from_token(response_data["idToken"])
        response_data["email_verified"] = user_info["email_verified"]
        return create_response_with_token(response_data, response_code)

    return response_data, response_code


@auth_api.route("/api/user", methods=["GET"])
@check_authenticated
def get_user():
    uid = request.user["uid"]
    return firebase.get_user(uid), HTTPStatus.OK


@auth_api.route("/api/user/<uid>", methods=["GET"])
@check_authenticated
def get_user_with_uid(uid: str):
    return firebase.get_user(uid), HTTPStatus.OK


@auth_api.route("/api/user/update", methods=["PATCH"])
@check_authenticated
def update_user():

    uid = request.user["uid"]
    avatar = request.json["avatar"]
    current_password = request.json["currentPassword"]
    new_password = request.json["newPassword"]

    if avatar:
        firebase.update_avatar(uid, avatar)

    if new_password:
        user_record = firebase.get_user(uid)
        credential_json = {
            "email": user_record["email"],
            "password": current_password,
        }

        # attempt to log in to check old password
        response_data, response_code = handle_auth_request(
            firebase.firebase_accounts_api(method="signInWithPassword"), credential_json
        )

        if response_code != HTTPStatus.OK:
            return response_data, HTTPStatus.BAD_REQUEST

        firebase.update_password(uid, new_password)

    return "Success", HTTPStatus.OK


@auth_api.route("/api/logout", methods=["POST"])
def logout():
    resp = make_response("Deleting idToken")
    resp.set_cookie("idToken", "", max_age=0)
    return resp


def handle_auth_request(request_url: str, request_json: dict):
    response = requests.post(request_url, json=request_json)
    response_data = response.json()

    if "error" in response_data:
        error_message = response_data["error"]["message"]
        error_message = firebase.error_messages.get(error_message, error_message)
        return error_message, response_data["error"]["code"]

    return response_data, response.status_code


def create_response_with_token(response_data, response_code):
    response = make_response(json.dumps(response_data), response_code)
    response.mimetype = "application/json"
    token_expire_date = datetime.datetime.now() + datetime.timedelta(days=90)
    response.set_cookie("idToken", response_data["idToken"], expires=token_expire_date)
    return response
