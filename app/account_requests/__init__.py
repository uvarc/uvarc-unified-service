from flask import Blueprint

account_requests = Blueprint('account_requests', __name__, __name__, url_prefix='/uvarc/api/accounts')
from app.account_requests import views