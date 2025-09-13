from flask_restful import Resource
from flask import request, make_response, jsonify, abort
from app import app
import logging
from app.workshop_visualization.business import UVARCWorkshopVisualizationDataManager, UVARCWorkshopSurveyDataManager
from common_utils import cors_check

class UVARCWorkshopAttendanceVisualizationEndpoint(Resource):

    def options(self):
        try:
            if cors_check(app, request.headers.get('Origin')):
                abort(401)
            else:
                response = jsonify({})
                response.headers.add('Origin', request.host_url)
                response.headers.add('Access-Control-Allow-Origin', request.headers.get('Origin'))
                response.headers.add('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept')
                response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
                response.headers.add('Access-Control-Allow-Credentials', 'true')
                return response
        except Exception as ex:
            response = make_response(jsonify(
                {
                    "status": "error",
                    "message": str(ex)
                }
            ), 400)
            response.headers.add('Access-Control-Allow-Credentials', 'true')
            return response

    def get(self):
        try:
            if cors_check(app, request.headers.get('Origin')):
                abort(401)
            else:
                data_helper = UVARCWorkshopVisualizationDataManager()
                response = make_response(jsonify(data_helper.merge_workshop_attendance_data(data_helper.get_workshop_data(), data_helper.get_attendance_data())), 200)
                response.headers.add('Access-Control-Allow-Credentials', 'true')
                return response
        except Exception as e:
            response = make_response({"error": str(e)}, 500)
            response.headers.add('Access-Control-Allow-Credentials', 'true')
            return response

class UVARCWorkshopSurveyVisualizationEndpoint(Resource):
    
    def options(self):
        try:
            if cors_check(app, request.headers.get('Origin')):
                abort(401)
            else:
                response = jsonify({})
                response.headers.add('Origin', request.host_url)
                response.headers.add('Access-Control-Allow-Origin', request.headers.get('Origin'))
                response.headers.add('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept')
                response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
                response.headers.add('Access-Control-Allow-Credentials', 'true')
                return response
        except Exception as ex:
            response = make_response(jsonify(
                {
                    "status": "error",
                    "message": str(ex)
                }
            ), 400)
            response.headers.add('Access-Control-Allow-Credentials', 'true')
            return response

    def post(self):
        try:
            if cors_check(app, request.headers.get('Origin')):
                abort(401)
            else:
                logging.info(f"Fetching survey data for survey ID: {app.config['WORKSHOP_SURVEY_ID']}")
                data_helper = UVARCWorkshopSurveyDataManager(app.config['WORKSHOP_SURVEY_ID'])
                logging.info(f"Fetched survey data: {len(data_helper.get_workshop_survey_data())}")
                response = make_response(jsonify(data_helper.get_workshop_survey_data()), 200)
                response.headers.add('Access-Control-Allow-Credentials', 'true')
                logging.info(f"Response length: {len(response.get_data(as_text=True))}")
                return response
        except Exception as e:
            response = make_response({"error": str(e)}, 500)
            response.headers.add('Access-Control-Allow-Credentials', 'true')
            return response

