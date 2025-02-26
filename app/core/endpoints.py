from flask_restful import Resource
from flask import g, request, make_response, jsonify
from datetime import datetime
from app import mongo_service
from app.core.business import UVARCUsersDataManager
