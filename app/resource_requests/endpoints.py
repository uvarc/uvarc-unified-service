from flask_restful import Resource
from flask import g, request, make_response, jsonify
from datetime import datetime
from app.resource_requests.business import UVARCResourcRequestFormInfoDataManager


class UVARCResourcRequestFormInfoEndpoint(Resource):
    # @api.param('uid', 'The user ID')
    def get(self, uid=None):
        """
        This is a resource request form endpoint that returns all data required for display and processing the form request!'
        ---
        responses:
            200:
                description: Returns formatted user information to display on rcweb resource request form
                schema:
                    type: array
                    items:
                        type: object
                        properties:
                        is_user_resource_request_elligible:
                            type: boolean
                        user_groups:
                            type: array
                examples:
                    application/json: [{"is_user_resource_request_elligible":false,"user_groups":["xyz","abc","pqr","cars","buses"]}]
            400:
                description: An error response
                examples:
                    application/json: "error!"
        """
        try:
            return make_response(
                jsonify(
                    UVARCResourcRequestFormInfoDataManager(uid).get_resource_request_from_info(request),
                    200
                )
            )
        except Exception as ex:
            return make_response(jsonify(
                {
                    "status": "error",
                    "message": str(ex)
                }
            ), 400)

    def options(self, uid=None):
        """
        This is a resource request form endpoint that returns all data required for display and processing the form request!'
        ---
        responses:
            200:
                description: Returns 200 for a preflight options call
        """
        try:
            response = jsonify({})
            response.headers.add('Access-Control-Allow-Origin', app.config['CORS_ENABLED_ALLOWED_ORIGINS'][0])
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
            response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
            return response
        except Exception as ex:
            return make_response(jsonify(
                {
                    "status": "error",
                    "message": str(ex)
                }
            ), 400)


class StorageRequestEndpoint(Resource):
    def get(self):
        """
        This is a storage request endpoint that returns 'Storage request received!'
        ---
        responses:
            200:
                description: A successful response
                examples:
                    application/json: "Storage request received!"
            400:
                description: An error response
                examples:
                    application/json: "error!"
        """
        try:
            return 'Storage request received implementation wip!'
        except Exception as ex:
            return make_response(jsonify(
                {
                    "status": "error",
                    "message": str(ex)
                }
            ), 400)
