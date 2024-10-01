from flask import Blueprint

allocation_requests = Blueprint('allocation_requests', __name__,url_prefix='/uvarc/api/allocation')
from app.resource_requests import views