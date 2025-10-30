from common_utils.auth import decode_auth_token
import flask_restful
import app
from flask import g, jsonify, request
import jwt
from app import auth, app


class SessionStatusEndpoint(flask_restful.Resource):
    """
    Returns the timecode (in seconds) when the current session expires,
    or 0 if there is no current session.
    """

    @auth.login_required
    def get(self):
        # We don't need to send in the auth token as an argument, it is in the
        # header.
        auth_token = request.headers['AUTHORIZATION'].split(' ')[1]
        if "user" in g and auth_token:
            try:
                payload = decode_auth_token(app, auth_token, True)
                # payload = jwt.decode(
                #     auth_token,
                #     app.config.get('SECRET_KEY'),
                #     algorithms='HS256')
                return payload['exp']
            except Exception as e:
                app.log_exception(e)
                return 0
        else:
            return 0
