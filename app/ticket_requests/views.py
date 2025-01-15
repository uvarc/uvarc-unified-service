import urllib
import flask_restful
from flask import jsonify, render_template, request, url_for
from flask_restful import reqparse

from app import app
from app.ticket_requests.business import GeneralSupportRequestManager
from . import ticket_requests
from common_utils.rest_exception import UVARCUnifiedApi
from app.ticket_requests.endpoints import UVARCUserOfficeHoursEndpoint, UVARCUsersOfficeHoursEndpoint
from app.ticket_requests.endpoints import GeneralSupportRequestEndPoint, SendMesaageEndPoint, ReceiveMesaageEndPoint



api = UVARCUnifiedApi(ticket_requests)

parser = flask_restful.reqparse.RequestParser()
parser.add_argument('resource')

endpoints = [
    (UVARCUserOfficeHoursEndpoint, '/officehours/get_user_details'),
    (UVARCUsersOfficeHoursEndpoint, '/officehours/get_users_details'),
    (GeneralSupportRequestEndPoint, '/officehours/general_support_ticket'),
    (SendMesaageEndPoint, '/officehours/send-message'),
    (ReceiveMesaageEndPoint, '/officehours/read-message')
]


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', logo_url=app.config['RC_SMALL_LOGO_URL'], ticket_id='5000', request_type='270', group_name='test')


@app.route('/message', methods=['GET'])
def message():
    return render_template('message.html', logo_url=app.config['RC_SMALL_LOGO_URL'], error_message="An error occurred while processing your request.")


@app.route('/submit', methods=['POST'])
def submit_form():
    try:
        response = GeneralSupportRequestManager().update_resource_request_status(request.form)
        print(response)
        return render_template('message.html', logo_url=app.config['RC_SMALL_LOGO_URL'], message="Message Sent Successfully!"), 200
    except Exception as e:
        print(e)
            # Handle AWS SQS errors
        return render_template('message.html', logo_url=RC_SMALL_LOGO_URL, message="An error occurred while sending the message"), 500


@ticket_requests.route('/', methods=['GET'])
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