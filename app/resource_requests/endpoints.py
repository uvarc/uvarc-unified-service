import pymongo
import flask_restful
from flask import g, request, make_response, jsonify
from app import app


class StorageRequestEndpoint(flask_restful.Resource):
    def get(self):
        try:
            return 'Storage request received'
        except Exception as ex:
            return make_response(jsonify(
                {
                    "status": "error",
                    "message": str(ex)
                }
            ), 400)
