from flask_restful import Resource
from flask import g, request, redirect, make_response, jsonify
from datetime import datetime
from app import mongo_service
from app.ticket_requests.business import UVARCUsersOfficeHoursDataManager
from app.ticket_requests.business import GeneralSupportRequestManager


class UVARCUserOfficeHoursEndpoint(Resource):
    def get(self):
        if mongo_service is None:
            return {"error": "MongoDB connection failed"}, 500

        get_info_helper = UVARCUsersOfficeHoursDataManager()

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


class UVARCUsersOfficeHoursEndpoint(Resource):
    def get(self):
        if mongo_service is None:
            return {"error": "MongoDB connection failed"}, 500

        get_info_helper = UVARCUsersOfficeHoursDataManager()

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


class GeneralSupportRequestEndPoint(Resource):
    def post(version='v2'):
        try:
            response = GeneralSupportRequestManager().process_support_request(
                request.form, request.host_url, version)
            return response
        except Exception as ex:
            print(ex)


class SendMesaageEndPoint(Resource):
    def post(version='v2'):
        data = request.get_json()
        try:
            response = GeneralSupportRequestManager().update_resource_request_status(data)
            return response
        except Exception as e:
            # Handle AWS SQS errors
            return jsonify({"error": str(e)}), 500
        

class ReceiveMesaageEndPoint(Resource):
    def get(self):
        try:
            response = GeneralSupportRequestManager().receive_message()
            return response
        except Exception as e:
            return jsonify({"error": str(e)}), 500




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
