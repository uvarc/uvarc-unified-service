import flask_restful
from flask import Blueprint, g, jsonify
from flask_restful import reqparse
from flask.helpers import make_response

class UVARCUnifiedApi(flask_restful.Api):
    # Define a custom error handler for all rest endpoints that
    # properly handles the RestException status.
    def handle_error(self, e):
        response = jsonify({
            "status": "error",
            "message": "Couldn't process request: "+str(e)
        })
        response.status_code = 400
        return make_response(response, 400)

class RestException(Exception):
    status_code = 400
    NOT_FOUND = {'code': 'not_found',
                 'message': 'Unknown path.', 'status_code': 404}
    TOKEN_INVALID = {'code': 'token_invalid',
                     'message': 'Please log in again.'}
    EMAIL_TOKEN_INVALID = {'code': 'email_token_invalid',
                           'message': 'Your email was not validated.  Please try resetting your password to continue.'}
    TOKEN_EXPIRED = {'code': 'token_expired',
                     'message': 'Your session timed out.  Please log in again.'}
    TOKEN_MISSING = {'code': 'token_missing',
                     'message': 'You are not logged in.'}
    ELASTIC_ERROR = {'code': 'elastic_error',
                     'message': "Error connecting to ElasticSearch."}
    NOT_YOUR_ACCOUNT = {'code': 'permission_denied',
                        'message': 'You may not edit another users account.'}
    PERMISSION_DENIED = {'code': 'permission_denied',
                         'message': 'You are not authorized to make this call.'}
    INVALID_OBJECT = {'code': 'invalid_object',
                      'message': 'Unable to save the provided object.'}
    CAN_NOT_DELETE = {'code': 'can_not_delete',
                      'message': 'You must delete all dependent records first.'}
    LOGIN_FAILURE = {'code': 'login_failure',
                     'message': 'The credentials you supplied are incorrect.'}
    EMAIL_EXISTS = {'code': 'duplicate_email',
                    'message': 'The email you provided is already in use.'}
    CONFIRM_EMAIL = {'code': 'confirm_email',
                     'message': 'You must confirm your email address before signing in.'}

    def __init__(self, payload, status_code=None, details=None):
        Exception.__init__(self)
        if 'status_code' in payload:
            self.status_code = payload['status_code']
        if status_code is not None:
            self.status_code = status_code
        if details is not None:
            payload['details'] = details
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload)
        return rv
