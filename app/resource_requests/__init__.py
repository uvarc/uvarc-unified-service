from flask import Blueprint

allocation_requests = Blueprint('allocation_requests', __name__,url_prefix='/uvarc/api/resource')
from app.resource_requests import views