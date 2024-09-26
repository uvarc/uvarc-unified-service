from flask import Blueprint

ldap_requests = Blueprint('ldap_requests', __name__, __name__, url_prefix='/uvarc/api/ldap')
from app.ldap_requests import views