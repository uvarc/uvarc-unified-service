# Login
# *****************************
from typing import Any


from functools import wraps
from app.core.business import UVARCUserDataManager
from common_utils.rest_exception import RestException
from flask.helpers import make_response

from app import app, auth, sso
import jwt
from bson.json_util import dumps
from json import loads

print(app.config)
from flask import Blueprint, jsonify, redirect, g, request

from datetime import datetime, timezone, timedelta
auth_blueprint = Blueprint('auth', __name__, url_prefix='/api')


def encode_auth_token(app, user):
    try:
        iat = datetime.now(timezone.utc)
        exp = iat + timedelta(hours=2, minutes=0, seconds=0)
        payload = {'exp': exp, 'iat': iat, 'sub': dumps(user)}
        return jwt.encode(
            payload, app.config['SECRET_KEY'], algorithm='HS256')
    except Exception as e:
        return e


def decode_auth_token(app, auth_token, is_raw_payload=False):
    try:
        payload = jwt.decode(
            auth_token, app.config['SECRET_KEY'], algorithms='HS256')
        if is_raw_payload:
            return payload
        else:
            return loads(payload['sub'])
    except jwt.ExpiredSignatureError:
        raise RestException(RestException.TOKEN_EXPIRED)
    except jwt.InvalidTokenError:
        raise RestException(RestException.TOKEN_INVALID)


@sso.login_handler
def login(user_info):
    if app.config['DEBUG']:
        for key in request.environ:
            print('ENVIRON -> {} : {}'.format(key, request.environ[key]))
        for key in user_info:
            print('USER_INFO -> {} : {}'.format(key, user_info[key]))
    if ('eppn' not in user_info or user_info[
        'eppn'] is None or len(user_info['eppn'].lstrip()) == 0) and 'SSO_DEVELOPMENT_EPPN' in app.config:
        user_info['eppn'] = app.config['SSO_DEVELOPMENT_EPPN']
        user_info['email'] = user_info['eppn']
        user = UVARCUserDataManager(uid=app.config['SSO_DEVELOPMENT_EPPN'].split('@')[0], upsert=True, refresh=True).get_user_info()
        user_info['uid'] = user['uid']
        user_info['display_name'] = user['displayName']
        user_info['title'] = user['title']
        user_info['department'] = user['department']

    g.user = user_info
    auth_token = encode_auth_token(app, user_info)
    response_url = (
        '%s/%s' % (app.config['FRONTEND_AUTH_CALLBACK'], auth_token))
    # print('URL RESPONSE: ', response_url)
    return redirect(response_url)


@auth.verify_token
def verify_token(token):
    try:
        resp = decode_auth_token(app, token)
        if resp:
            g.user = resp
    except Exception as ex:
        print(str(ex))
        g.user = None

    if 'user' in g and g.user:
        return True
    else:
        return False


@auth.get_user_roles
def get_user_roles(user):
    resp = decode_auth_token(app, user['token'])
    if resp:
        user_admin_roles = ['']
        # user_admin_roles = fetch_user_roles(g.user['eppn'])
        if request.view_args and 'project_id' in request.view_args:
            # return user_admin_roles + fetch_user_roles(str(g.user['eppn']), str(request.view_args['project_id']))
            return user_admin_roles
        else:
            return user_admin_roles
    else:
        return ['']


@auth.error_handler
def unauthorized():
    return make_response(jsonify({'message': 'You are not authorized, please contact system admin'}), 403)


def login_optional(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.method != 'OPTIONS':  # pragma: no cover
            try:
                auth = verify_token(
                    request.headers['AUTHORIZATION'].split(' ')[1])
            except Exception as ex:
                print(str(ex))
                auth = False

        return f(*args, **kwargs)

    return decorated
