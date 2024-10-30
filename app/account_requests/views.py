import urllib
import flask_restful
from flask import jsonify, url_for
from flask_restful import reqparse

from app import app
from . import account_requests
from common_utils.rest_exception import UVARCUnifiedApi

api = UVARCUnifiedApi(account_requests)

parser = flask_restful.reqparse.RequestParser()
parser.add_argument('resource')

endpoints = [

]


@account_requests.route('/', methods=['GET'])
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