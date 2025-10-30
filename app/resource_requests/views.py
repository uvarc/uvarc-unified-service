import urllib
# import flask_restful
from app.resource_requests.session_endpoint import SessionEndpoint
from app.resource_requests.session_status_endpoint import SessionStatusEndpoint
from flask import jsonify, url_for
from flask_restful import reqparse
# from flask_restx import reqparse

from app import app
from . import resource_requests
from common_utils.rest_exception import UVARCUnifiedApi
from app.resource_requests.endpoints import UVARCAdminFormInfoEndpoint, UVARCAdminFormStatusUpdateEndpoint, UVARCFDMValidorEndpoint, UVARCResourcRequestFormInfoEndpoint


api = UVARCUnifiedApi(resource_requests)

parser = reqparse.RequestParser()
parser.add_argument('resource')

endpoints = [
    (SessionEndpoint, '/session'),
    (SessionStatusEndpoint, '/sessionstatus'),
    (UVARCAdminFormInfoEndpoint, '/rcadminform/group/<group_name>'),
    (UVARCAdminFormStatusUpdateEndpoint, '/rcadminform/group/update'),
    (UVARCFDMValidorEndpoint, '/rcwebform/fdm/verify'),
    (UVARCResourcRequestFormInfoEndpoint, '/rcwebform/user/<uid>')
]


@resource_requests.route('/', methods=['GET'])
def root():
    output = {}
    for rule in app.url_map.iter_rules():
        options = {}
        for arg in rule.arguments:
            options[arg] = "<{0}>".format(arg)

        methods = ','.join(rule.methods)
        url = url_for(rule.endpoint, **options)
        output[rule.endpoint] = urllib.parse.unquote(url)

    return jsonify(output)


for endpoint in endpoints:
    api.add_resource(endpoint[0], endpoint[1])
