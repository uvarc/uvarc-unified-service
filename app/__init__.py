import logging
import os
import signal

from datetime import timedelta
from flask import Flask, abort, jsonify, request
from celery import Celery
from flasgger import Swagger
from celery.schedules import crontab
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_httpauth import HTTPTokenAuth
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_marshmallow import Marshmallow
from flask_pymongo import PyMongo
from flask_sso import SSO
# from common_service_handlers.aws_service_handler import AWSServiceHandler
# from common_service_handlers.kube_service_handler import KubeService
# from common_service_handlers.email_service_handler import EmailService
# from app.ldap_requests.business import LDAPSyncJobBusinessLogic
from common_service_handlers.jira_service_handler import JiraServiceHandler
from common_utils.rest_exception import RestException


template = {
    "swagger": "2.0",
    "info": {
        "title": "UVARC Unified services APIs",
        "description": "This API provides an unified set of endpoints to support Research Computing automation needs.",
        "version": "1.0"
    }
}

app = Flask(__name__, instance_relative_config=True)

# Load the configuration from the instance folder
app.config.from_pyfile('settings.py')

if (app.config['DEBUG']):
    app.debug = True
    log_level = logging.DEBUG
else:
    log_level = logging.INFO

logging.basicConfig(filename='/var/log/uvarc_unified_service.log', level=log_level,
                    format=f'%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')

# Enable CORS
# if (app.config['CORS_ENABLED']):
#     cors = CORS(
#         app=app, 
#         origins=app.config['CORS_ENABLED_ALLOWED_ORIGINS'], 
#         supports_credentials=True
#     )
# else:
#     cors = CORS(app=app)

# Flask-Marshmallow provides HATEOAS links
ma = Marshmallow(app)

# # email service
# email_service = EmailService(app)

# Single Signon
sso = SSO(app=app)

# Token Authentication
auth = HTTPTokenAuth('Bearer')

# Password Encryption
bcrypt = Bcrypt(app)
mongo_service = PyMongo(app)
# kube_service = KubeService(app)
# aws_service = AWSServiceHandler(app)
jira_service = JiraServiceHandler(app)

limiter = Limiter(key_func=get_remote_address)
limiter.init_app(app)

celery = Celery(
    app.name,
    broker=app.config['CELERY_BROKER_URL']
)
celery.conf.result_backend = app.config['CELERY_BROKER_URL']
celery.conf.mongodb_backend_settings = app.config['CELERY_BACKEND_SETTINGS']
celery.conf.beat_schedule = app.config['CELERY_BEAT_SCHEDULE']
celery.conf.task_track_started = True
celery.conf.worker_send_task_events = True
celery.conf.broker_connection_retry_on_startup = True
celery.conf.update(app.config)

#Swagger setup
app.config['SWAGGER'] = {
    'title': 'UVARC Unified services APIs',
    'uiversion': 2,
    'template': './resources/flasgger/swagger_ui.html'
}
swagger = Swagger(app, template=template)


def handler(error, endpoint, values=''):
    print('URL Build error:' + str(error))
    return ''
app.url_build_error_handlers.append(handler)


@app.before_request
def before_request():
    abort_flag = True
    for allowed_url in app.config['CORS_ENABLED_ALLOWED_ORIGINS']:
        if allowed_url in request.host_url:
            abort_flag = False
    if abort_flag:
        abort(401)

# Handle errors consistently
@app.errorhandler(RestException)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.errorhandler(404)
def handle_404(error):
    return handle_invalid_usage(RestException(RestException.NOT_FOUND, 404))

# @app.cli.command()
# def initdb():
#     ldap_sync = LDAPSyncJobBusinessLogic(app)
#     ldap_sync.backfill_users_info()

@app.cli.command()
def stop():
    """Stop the server."""
    pid = os.getpid()
    if pid:
        print('Stopping server...')
        os.kill(pid, signal.SIGTERM)
        print('Server stopped.')
    else:
        print('Server is not running.')

from app.account_requests import account_requests
from app.resource_requests import allocation_requests
from app.ticket_requests import ticket_requests
app.register_blueprint(account_requests)
app.register_blueprint(allocation_requests)
app.register_blueprint(ticket_requests)


from app.account_requests import tasks
from app.resource_requests import tasks
from app.ticket_requests import tasks
from common_utils import tasks
