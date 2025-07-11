from flask_restful import Resource
from app import app
from app.workshop_visualization.business import UVARCWorkshopVisualizationDataManager, UVARCWorkshopSurveyDataManager

class UVARCWorkshopAttendanceVisualizationEndpoint(Resource):

    def get(self):
        try:
            data_helper = UVARCWorkshopVisualizationDataManager()
            return data_helper.merge_workshop_attendance_data(data_helper.get_workshop_data(), data_helper.get_attendance_data()), 200
        except Exception as e:
            return {"error": str(e)}, 500

class UVARCWorkshopSurveyVisualizationEndpoint(Resource):
    
    def get(self):
        try:
            data_helper = UVARCWorkshopSurveyDataManager(app.config['WORKSHOP_SURVEY_ID'])
            return data_helper.get_workshop_survey_data(), 200
        except Exception as e:
            return {"error": str(e)}, 500

