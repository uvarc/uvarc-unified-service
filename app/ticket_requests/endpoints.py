from flask_restful import Resource
from flask import request, make_response, jsonify
from app.ticket_requests.business import CreateTicketBusinessLogic

# class CreateTicketEndpoint(flask_restful.Resource):
#     def get(self):
#         try:
#             return 'Tickets request received'
#         except Exception as ex:
#             return make_response(jsonify(
#                 {
#                     "status": "error",
#                     "message": str(ex)
#                 }
#             ), 400)

class CreateTicketEndpoint(Resource):
    def post(self):
        try:
            form_data = request.json
            if not form_data:
                return {"error": "No data provided"}, 400
            
            ticket_logic = CreateTicketBusinessLogic()
            ticket_data = ticket_logic.create_ticket(form_data)
            
            return {"data": ticket_data}, 200  #####

        except Exception as ex:
            return make_response(jsonify({"status": "error", "message": str(ex)}), 400)