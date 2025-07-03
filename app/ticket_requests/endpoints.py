# from app.resource_requests.business import UVARCAdminFormInfoDataManager
from flask_restful import Resource
from app import app,logging
from flask import g, json, render_template, request, redirect, make_response, url_for, abort
from flask import jsonify
from datetime import datetime
from app import mongo_service
from app.ticket_requests.business import UVARCUsersOfficeHoursDataManager, UVARCSupportRequestsManager
RC_SMALL_LOGO_URL = 'https://staging.rc.virginia.edu/images/logos/uva_rc_logo_full_340x129.png'
from common_utils import cors_check
from common_utils.business import UVARCUserInfoManager


class UVARCUserInfoEndpoint(Resource):

    def get(self):
        """
        This endpoint retrieves detailed information for one user, including historical data if a specific time is provided.

        ---
        parameters:
            - in: query
            name: id
            required: true
            type: string
            description: The unique identifier of the user whose data is being queried.
            - in: query
            name: time
            required: false
            type: string
            format: date-time
            description: A specific time in ISO format (YYYY-MM-DD) to filter historical data.

        responses:
            200:
                description: Returns detailed user information.
            400:
                description: An error response due to a missing or invalid query parameter.
                examples:
                    application/json: {"error": "No query parameter 'id' found"}
            500:
                description: An error response indicating a failure in connecting to MongoDB.
                examples:
                    application/json: {"error": "MongoDB connection failed"}
        """

        if mongo_service is None:
            return {"error": "MongoDB connection failed"}, 500

        get_info_helper = UVARCUserInfoManager()

        id = request.args.get("id")
        if not id:
            return {"error": "No query parameter 'id' found"}, 400

        time = request.args.get("time")

        # Logic for grabbing recent time if included as query parameter
        if time:
            try:
                query_time = datetime.fromisoformat(time)
            except ValueError:
                return {"error": "Invalid time format. Use ISO format: YYYY-MM-DD"}, 400

            return {"data": get_info_helper.get_user_hist_info(id, query_time)}, 200

        # default approach
        return {"data": get_info_helper.get_user_info(id)}, 200


class UVARCUsersInfoEndpoint(Resource):
    """
    This endpoint retrieves detailed user information, including historical data if a specific time is provided. Supports multiple user IDs as a comma-separated list.

    ---
    parameters:
        - in: query
        name: ids
        required: true
        type: string
        description: A comma-separated list of unique identifiers for the users whose data is being queried.
        - in: query
        name: time
        required: false
        type: string
        format: date-time
        description: A specific time in ISO format (YYYY-MM-DD) to filter historical data.

    responses:
        200:
            description: Returns detailed user information for the specified user IDs.
        400:
            description: An error response due to a missing or invalid query parameter.
        500:
            description: An error response indicating a failure in connecting to MongoDB.
    """

    def get(self):
        if mongo_service is None:
            return {"error": "MongoDB connection failed"}, 500

        get_info_helper = UVARCUserInfoManager()

        ids = request.args.get("ids")
        if not ids:
            return {"error": "No query parameter 'id' found"}, 400

        time = request.args.get("time")
        list_of_ids = ids.split(',')

        # Logic for grabbing recent time if included as query parameter
        if time:
            try:
                query_time = datetime.fromisoformat(time)
            except ValueError:
                return {"error": "Invalid time format. Use ISO format: YYYY-MM-DD"}, 400

            response_data = []
            for id in list_of_ids:
                response_data.append(
                    get_info_helper.get_user_hist_info(id, query_time))
            return {"data": response_data}, 200

        response_data = []
        for id in list_of_ids:
            response_data.append(get_info_helper.get_user_info(id))

        return {"data": response_data}, 200


class UVARCOfficeHoursFormEndpoint(Resource):
    """
    This endpoint creates a ticket for office hours based on the provided form data.

    ---

    responses:
        200:
            description: Returns the created ticket data.
            schema:
                type: object
                properties:
                    data:
                        type: object
                        description: The details of the successfully created ticket.
        400:
            description: An error response due to invalid input or missing data.
    """
    def post(self):
        try:
            if cors_check(app, request.headers.get('Origin')):
                abort(401)
            else:
                form_data = request.json
                if not form_data:
                    return {"error": "No data provided"}, 400
                
                ticket_logic = UVARCUsersOfficeHoursDataManager()
                ticket_response, ticket_data = ticket_logic.create_officehour_ticket(form_data)
                response = None
                if not ticket_response:
                    logging.error("Something went wrong!", exc_info=True)
                    response = make_response({"error": ticket_data}, 400)
                else: 
                    response = make_response({"data": ticket_data}, 200) 
                response.headers.add('Access-Control-Allow-Credentials', 'true')
                return response

        except Exception as ex:
            # add in logger that adds in stack trace [ex], so don't typecast it here
            logging.error("Caught exception: %s", ex)
            return make_response(jsonify({"status": "error", "message": str(ex)}), 400)
        
    def options(self):
        """
        This is the office hours preflight option call'
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


class AdminPagesEndPoint(Resource):
    def get(self):
        return make_response(render_template('index.html', logo_url=app.config['RC_SMALL_LOGO_URL']))


class AdminPagesEndPointWithTabId(Resource):
    def get(self, tab_index=0):
        return make_response(render_template('index.html', 
                                             logo_url=app.config['RC_SMALL_LOGO_URL'],
                                             tab_index=tab_index))


class GroupClaimEndPoint(Resource):
    def post(self):
        try:
            if cors_check(app, request.headers.get('Origin')):
                abort(401)
            else:
                request_payload = request.get_json()
                uid = request_payload.get('uid')
                group_name = request_payload.get('group_name')
                support_request_type = 'General'
                ticket_request_payload = {
                    'uid': uid if uid is not None and uid is not '' else make_response(jsonify({"status": "error", "message": "Cannot process the PI's claim request: UserID is required"}), 400),
                    'grpup_name':  group_name if group_name is not None and group_name is not '' else make_response(jsonify({"status": "error", "message": "Cannot process the claim request: Group Name is required"}), 400),
                    'request_type': 'PI Group Claim',
                    'claim_approval_url': "{host_url}uvarc/api/ticket/admin/mgmt/1?group_name={group_name}&owner_uid={uid}".format(host_url=request.host_url, group_name=group_name, uid=uid),
                }

                ticket_response = UVARCSupportRequestsManager().create_support_request(
                    support_request_type,
                    ticket_request_payload
                )
                if isinstance(ticket_response, str):
                    ticket_response = json.loads(ticket_response)

                response = jsonify(
                    {
                        "status": "success",
                        'message': 'Group claim request (TicketID: {ticket_id}) successfully submitted'.format(ticket_id=ticket_response['issueKey'])
                    },
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

    def options(self):
        """
        This is the office hours preflight option call'
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



# class GetLDAPUserInfoEndpoint(Resource):
#     def get(self):

#         ids = request.args.get("ids")
#         if not ids:
#             return {"error": "No query parameter 'id' found"}, 400

#         list_of_ids = ids.split(",")

#         all_ldap_info = {}

#         for uid in list_of_ids:
#             uid_ldap_info = get_combined_ldap_info(uid)
#             all_ldap_info[uid] = uid_ldap_info


#         return all_ldap_info,200


# class UpdateDBWithLDAPInfoEndpoint(Resource):
#     def post(self):

#         data = request.json
#         if not data:
#             return {"error": "No data provided"}, 400

#         ids = data.get("ids")
#         if not ids:
#             return {"error": "No 'ids' field found in request body"}, 400

#         uid_list = ids.split(",")

#         ldap = LDAPServiceHandler()

#         eservices_conn = ldap.create_eservices_ldap_connection()
#         public_conn = ldap.create_public_ldap_connection()

#         users = mongo.db.users

#         for uid in uid_list:
#             combined_ldap_entry = get_combined_ldap_info(uid, eservices_conn, public_conn)["uid"]

#             user = users.find_one({"UserID": uid})

#             if combined_ldap_entry:
#                 combined_ldap_entry = format_dates_for_input(combined_ldap_entry)
#                 if user:
#                     # if no changes, then no dictionary is sent back
#                     changed_fields =  DeepDiff(user["recent_ldap_info"], combined_ldap_entry, exclude_paths="root['date_of_query']")

#                     if changed_fields:
#                         user["ldap_info_log"].append(user["recent_ldap_info"])
#                         user["recent_ldap_info"] = combined_ldap_entry

#                         users.update_one(
#                             {"UserID": user["UserID"]},  # Filter to find the document
#                             {"$set": {
#                                 "ldap_info_log": user["ldap_info_log"],
#                                 "recent_ldap_info": user["recent_ldap_info"],
#                                 "date_modified": user["recent_ldap_info"]["date_of_query"],
#                                 "comments_on_changes": changed_fields["values_changed"]
#                             }
#                             }
#                         )
#                 else:
#                     users.insert_one(
#                                 {"UserID": combined_ldap_entry["uid"],
#                                     "recent_ldap_info": combined_ldap_entry,
#                                     "ldap_info_log": [],
#                                     "date_modified": combined_ldap_entry["date_of_query"],
#                                     "comments_on_changes": "Initial Entry"
#                                 }
#                             )


#         ldap.close_ldap_connection(eservices_conn)
#         ldap.close_ldap_connection(public_conn)

#         return {"message": "LDAP information successfully processed and updated."}, 200


# class LDAPUserInfoEndpoint(flask_restful.Resource):
#     def get(self):
#         try:
#             return 'LDAP request received'
#         except Exception as ex:
#             return make_response(jsonify(
#                 {
#                     "status": "error",
#                     "message": str(ex)
#                 }
#             ), 400)
