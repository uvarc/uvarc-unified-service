from flask_restful import Resource
from flask import abort, g, request, make_response, jsonify
from datetime import datetime
from app import app
from app.resource_requests.business import UVARCBillingInfoValidator, UVARCAdminFormInfoDataManager, UVARCResourcRequestFormInfoDataManager
from common_utils import cors_check


class UVARCAdminFormStatusUpdateEndpoint(Resource):
    def put(self):
        try:
            form_field_data = request.form
            UVARCAdminFormInfoDataManager(form_field_data['group_name']).update_resource_request_status(
                form_field_data['ticket_id'],
                form_field_data['resource_type'],
                form_field_data['resource_name'],
                form_field_data['update_status'],
                form_field_data['update_comment']
            )
            response = jsonify(
                {
                    "status": "success",
                    "message": 'Resource request status updated successfully!'
                }
            )
            return make_response(
                response,
                200
            )
            return {'message': ''}, 200
        except Exception as ex:
            print(ex)
            response = jsonify(
                {
                    "status": "error",
                    "message": str(ex)
                },
                400
            )
            return make_response(
                response
            )


class UVARCAdminFormInfoEndpoint(Resource):

    def get(self, group_name):
        """
        This is a resource request form endpoint to fetch group owner details!'
        ---
        responses:
            200:
                description: Returns
                    {
                        "is_owner_set": <true/false>,
                        "owner_uid": <uid>
                    }
            400:
                description: An error response
                examples:
                    application/json: "error!"
        """
        try:
            # if cors_check(app, request.headers.get('Origin')):
            #     abort(401)
            # else:
            if 'group_users_info' in request.args and request.args['group_users_info'] == 'true':
                response = jsonify(
                    UVARCAdminFormInfoDataManager(group_name).get_group_users_info(),
                    200
                )
            else:
                response = jsonify(
                    UVARCAdminFormInfoDataManager(group_name).get_group_admin_info(),
                    200
                )
            response.headers.add('Access-Control-Allow-Credentials', 'true')
            return make_response(
                response
            )
        except Exception as ex:
            response = jsonify(
                {
                    "status": "error",
                    "message": str(ex)
                },
                400
            )
            response.headers.add('Access-Control-Allow-Credentials', 'true')
            return make_response(
                response
            )

    def put(self, group_name):
        """
        This is a resource request form endpoint to update group ownwr!'
        ---
        responses:
            200:
                description: Returns true or false
            400:
                description: An error response
                examples:
                    application/json: "error!"
        """
        try:
            # if cors_check(app, request.headers.get('Origin')):
            #     abort(401)
            # else:
            group_info = request.get_json()
            UVARCAdminFormInfoDataManager(group_name).set_group_admin_info(group_info['owner_uid'])

            response = jsonify(
                {
                    "status": "success",
                    "message": 'Group owner updated successfully'
                }
            )
            response.headers.add('Access-Control-Allow-Credentials', 'true')
            return make_response(
                response,
                200
            )
        except Exception as ex:
            response = jsonify(
                {
                    "status": "error",
                    "message": str(ex)
                },
                400
            )
            response.headers.add('Access-Control-Allow-Credentials', 'true')
            return make_response(
                response
            )


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


class UVARCFDMValidorEndpoint(Resource):
    def post(self):
        """
        This is a resource request form endpoint validates FDM details!'
        ---
        responses:
            200:
                description: Returns true or false
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
                    UVARCBillingInfoValidator(request.get_json()).validate_fdm_info(),
                    200
                )
                response.headers.add('Access-Control-Allow-Credentials', 'true')
                return make_response(
                    response
                )
        except Exception as ex:
            response = jsonify(
                {
                    "status": "error",
                    "message": str(ex)
                },
                400
            )
            response.headers.add('Access-Control-Allow-Credentials', 'true')
            return make_response(
                response
            )

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


class UVARCResourcRequestFormInfoEndpoint(Resource):
    def post(self, uid=None):
        try:
            if cors_check(app, request.headers.get('Origin')):
                abort(401)
            else:
                resource_requests_info = request.get_json()
                app.logger.info("Form data create resource request received: {resource_requests_info}".format(resource_requests_info=resource_requests_info))
                if resource_requests_info and len(resource_requests_info) > 0:
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
                        "message": 'Create resource request submitted successfully'
                    }
                )
                response.headers.add('Access-Control-Allow-Credentials', 'true')
                return make_response(
                    response,
                    200
                )
        except Exception as ex:
            response = jsonify(
                {
                    "status": "error",
                    "message": str(ex)
                },
                400
            )
            response.headers.add('Access-Control-Allow-Credentials', 'true')
            return make_response(
                response
            )

    def put(self, uid=None):
        try:
            if cors_check(app, request.headers.get('Origin')):
                abort(401)
            else:
                resource_requests_info = request.get_json()
                app.logger.info("Form data update resource request received: {resource_requests_info}".format(resource_requests_info=resource_requests_info))
                if resource_requests_info and len(resource_requests_info) > 0:
                    for resource_request_info in resource_requests_info:
                        uvarc_resource_request_manager = UVARCResourcRequestFormInfoDataManager(uid)
                        if 'resources' in resource_request_info:
                            if 'hpc_service_units' in resource_request_info['resources']:
                                print(resource_request_info['resources']['hpc_service_units'])
                                uvarc_resource_request_manager.update_user_resource_su_request_info(resource_request_info)
                            elif 'storage' in resource_request_info['resources']:
                                print(resource_request_info['resources']['storage'])
                                uvarc_resource_request_manager.update_user_resource_storage_request_info(resource_request_info)
                response = jsonify(
                    {
                        "status": "success",
                        "message": 'Update resource request submitted successfully'
                    }
                )
                response.headers.add('Access-Control-Allow-Credentials', 'true')
                return make_response(
                    response,
                    200
                )
        except Exception as ex:
            response = jsonify(
                {
                    "status": "error",
                    "message": str(ex)
                },
                400
            )
            response.headers.add('Access-Control-Allow-Credentials', 'true')
            return make_response(
                response
            )

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
            response = jsonify(
                {
                    "status": "error",
                    "message": str(ex)
                },
                400
            )
            response.headers.add('Access-Control-Allow-Credentials', 'true')
            return make_response(
                response
            )

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

    def delete(self, uid=None):
        try:
            if cors_check(app, request.headers.get('Origin')):
                abort(401)
            else:
                group_name = request.args['group_name']
                resource_request_type = request.args['resource_request_type']
                resource_requst_name = request.args['resource_requst_name']

                app.logger.info("Form data retire resource request received: uid={uid} group_name={group_name} resource_request_type={resource_request_type} resource_requst_name={resource_requst_name}".format(uid=uid, group_name=group_name, resource_request_type=resource_request_type, resource_requst_name=resource_requst_name))
                uvarc_resource_request_manager = UVARCResourcRequestFormInfoDataManager(uid)
                if resource_request_type == 'hpc_service_units':
                    uvarc_resource_request_manager.retire_user_resource_su_request_info(group_name, resource_request_type, resource_requst_name)
                elif resource_request_type == 'storage':
                    uvarc_resource_request_manager.retire_user_resource_storage_request_info(group_name, resource_request_type, resource_requst_name)
                response = jsonify(
                    {
                        "status": "success",
                        "message": 'Retire resource request submitted successfully'
                    }
                )
                response.headers.add('Access-Control-Allow-Credentials', 'true')
                return make_response(
                    response,
                    200
                )
        except Exception as ex:
            response = jsonify(
                {
                    "status": "error",
                    "message": str(ex)
                },
                400
            )
            response.headers.add('Access-Control-Allow-Credentials', 'true')
            return make_response(
                response
            )
