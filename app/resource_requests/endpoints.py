import pymongo
import flask_restful
from flask import g, request, make_response, jsonify
from app import app


class StorageRequestEndpoint(flask_restful.Resource):
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
            return 'Storage request received!'
        except Exception as ex:
            return make_response(jsonify(
                {
                    "status": "error",
                    "message": str(ex)
                }
            ), 400)
