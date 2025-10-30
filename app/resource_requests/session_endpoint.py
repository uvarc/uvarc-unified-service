import flask_restful
import app
from flask import g, jsonify
from app import auth, logging
# from app.resource_requests import get_user_obj_by_eppn

def get_user_obj_by_eppn(eppn):
    # return UVARCUserDataManager(uid=eppn.split('@')[0], upsert=True, refresh=True).get_user_info()
    return None

class SessionEndpoint(flask_restful.Resource):
    """Provides a way to get the current user, and to delete the user."""

    @auth.login_required
    def get(self):
        if 'user' in g:
            user = {'uid': g.user['uid'], 'eppn': g.user['eppn'], 'display_name': g.user['display_name'], 'title': g.user['title']}
            user['roles'] =[]
            return user
        else:
            return None

    @staticmethod
    def delete():
        if 'user' in g:
            g.user = None
            app.logging.info("Session Endpoint: Removing the user from session")
        else:
            return None
