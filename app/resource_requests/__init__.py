from flask import Blueprint

resource_requests = Blueprint('resource_requests', __name__,url_prefix='/uvarc/api/resource')
from app.resource_requests import views


# def get_user_by_eppn(eppn):
#     return mongo.db.users.find_one({"email": eppn})

# def get_user_by_user_id(user_id):
#     user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
#     if user is not None:
#         user['_id'] = {'$oid': user_id}
#         user['user_update_by_user_id'] = {'$oid': user['user_update_by_user_id'].__str__()}
#         user['can_edit_user_permission'] = True if 'app-admin' in fetch_user_roles(user['email']) else False
#     return user


# def get_users():
#     users_db = mongo.db.users.find({}).sort([
#         ('_id', pymongo.DESCENDING),
#     ])
#     users = []
#     for user in users_db:
#         user['_id'] = {'$oid': user['_id'].__str__()}
#         user['user_update_by_user_id'] = {'$oid': user['user_update_by_user_id'].__str__()}
#         user['user_permissions'] = []
#         user_permissions = mongo.db.admins.find_one({"user_id": get_user_by_eppn(str(user['email']))['_id']})
#         if user_permissions is not None:
#             for admin_permission in user_permissions['admin_permissions']:
#                 user['user_permissions'].append({'user_role': admin_permission['admin_role']})
#         users.append(user)
#     return users


# def get_user_project_perm_flags(eppn, project_id, app_roles=()):
#     user_roles = app_roles + fetch_user_roles(eppn, project_id)
#     return {
#         'can_edit_project': True if 'project-admin' in user_roles else False,
#         'can_view_project': True if 'project-admin' in user_roles or 'project-user' in user_roles or 'app-admin' in user_roles or 'app-approver' in user_roles else False,
#         'can_archive_project': True if 'project-admin' in user_roles and 'project-pi' in user_roles else False,
#         'can_approve_project': True if 'app-approver' in user_roles else False,
#     }


# @dispatch(str, str)
# def fetch_user_roles(eppn, project_id):
#     user_roles = set()
#     project_roles_cursor = mongo.db.projects.find_one({'_id': ObjectId(project_id)})
#     if project_roles_cursor is not None and 'project_permissions' in project_roles_cursor:
#         for project_permission in project_roles_cursor['project_permissions']:
#             if project_permission["user_id"] == get_user_by_eppn(eppn)['_id']:
#                 user_roles.add(project_permission["user_role"])
#                 if project_permission["is_pi"]:
#                     user_roles.add('project-pi')

#     return tuple(user_roles)


# @dispatch(str)
# def fetch_user_roles(eppn):
#     admin_roles = set()
#     admin_roles_cursor = mongo.db.admins.find_one({"user_id": get_user_by_eppn(eppn)['_id']})
#     if admin_roles_cursor is not None and 'admin_permissions' in admin_roles_cursor:
#         for admin_permission in admin_roles_cursor['admin_permissions']:
#             admin_roles.add(admin_permission["admin_role"])

#     return tuple(admin_roles)
