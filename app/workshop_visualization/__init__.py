from flask import Blueprint

workshop_visualization = Blueprint('workshop_visualization', __name__, url_prefix='/uvarc/api/workshops')
from app.workshop_visualization import views
