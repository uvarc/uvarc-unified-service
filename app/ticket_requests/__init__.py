from flask import Blueprint

ticket_requests = Blueprint('ticket_requests', __name__, url_prefix='/uvarc/api/ticket')
from app.ticket_requests import views