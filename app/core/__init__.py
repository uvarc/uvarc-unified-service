from flask import Blueprint

core = Blueprint('core', __name__, __name__, url_prefix='/uvarc/api/accounts')
from app.core import views