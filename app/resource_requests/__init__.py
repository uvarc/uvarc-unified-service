from flask import Blueprint

allocation_requests = Blueprint('allocation_requests', __name__,url_prefix='/uvarc/api/allocation')
from app.allocation_requests import views