from flask_restful import Resource
from flask import abort, g, request, make_response, jsonify
from datetime import datetime
from app import app
from app.resource_requests.business import UVARCResourcRequestFormInfoDataManager
from common_utils import cors_check


class UVARCResourcRequestFormInfoEndpoint(Resource):
    def post(self, uid=None):
        try:
            if cors_check(app, request.headers.get('Origin')):
                abort(401)
            else:
                resource_requests_info = request.get_json()
                app.logger.info("Form data created resource received: {resource_requests_info}".format(resource_requests_info=resource_requests_info))
                if resource_requests_info and len(resource_requests_info) >0:
                    for resource_request_info in resource_requests_info:
                        uvarc_resource_request_manager = UVARCResourcRequestFormInfoDataManager(uid)
                        if 'resources' in resource_request_info:
                            if 'hpc_service_units' in resource_request_info['resources']:
                                print(resource_request_info['resources']['hpc_service_units'])
                                uvarc_resource_request_manager.create_user_resource_su_request_info(resource_request_info)
                            elif 'storage' in resource_request_info['resources']:
                                print(resource_request_info['resources']['storage'])
                                uvarc_resource_request_manager.create_user_resource_storage_request_info(resource_request_info)
                response = jsonify(
                    {
                        "status": "success",
                        "message": 'Request submitted successfully'
                    }
                )
                response.headers.add('Access-Control-Allow-Credentials', 'true')
                return make_response(
                    response
                )
        except Exception as ex:
            return make_response(jsonify(
                {
                    "status": "error",
                    "message": str(ex)
                }
            ), 400)

    def put(self, uid=None):
        try:
            if cors_check(app, request.headers.get('Origin')):
                abort(401)
            else:
                resource_requests_info = request.get_json()
                app.logger.info("Form data created resource received: {resource_request_info}".format(resource_request_info=resource_request_info))
                if resource_requests_info and len(resource_requests_info) >0:
                    for resource_request_info in resource_requests_info:
                        uvarc_resource_request_manager = UVARCResourcRequestFormInfoDataManager(uid)
                        if 'resources' in resource_request_info:
                            if 'hpc_service_units' in resource_request_info['resources']:
                                print(resource_request_info['resources']['hpc_service_units'])
                                uvarc_resource_request_manager.update_user_resource_su_request_info(resource_request_info)
                            elif 'storage' in resource_request_info['resources']:
                                print(resource_request_info['resources']['storage'])
                                uvarc_resource_request_manager.update_user_resource_storage_request_info(resource_request_info)
        except Exception as ex:
            return make_response(jsonify(
                {
                    "status": "error",
                    "message": str(ex)
                }
            ), 400)

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
            if cors_check(app, request.headers.get('Origin')):
                abort(401)
            else:
                
                response = jsonify(
                    UVARCResourcRequestFormInfoDataManager(uid).get_user_resource_request_info(),
                    200
                )
                response.headers.add('Access-Control-Allow-Credentials', 'true')
                return make_response(
                    response
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
