import json
import logging
import os
from datetime import timedelta

NAME = 'UVARC UNIFIED SERVICE'
VERSION = '0.1'


def fetch_connections_info():
    if 'SETTINGS_JSON' in os.environ:
        settings = json.loads(os.environ['SETTINGS_JSON'])
        settings["AWS"]['CLIENT_ID'] = os.environ['AWS_CLIENT_ID']
        settings["AWS"]['CLIENT_SECRET'] = os.environ['AWS_CLIENT_SECRET']
        settings["MONGODB"]['CLIENT_ID'] = os.environ['MONGO_USER']
        settings["MONGODB"]['CLIENT_SECRET'] = os.environ['MONGO_PASSWORD']
        return settings
    else:
        return json.load(open('./connections.json'))


def auth_callback_url_tuple(portal_host_url, auth_callback_route, auth_email_reset_route, auth_email_confirm_route): return (
    ''.join([portal_host_url, auth_callback_route]), ''.join([portal_host_url, auth_email_reset_route]), ''.join([portal_host_url, auth_email_confirm_route]))


settings_info = fetch_connections_info()
print(settings_info)

CORS_ENABLED = settings_info["CORS_ENABLED"]
DEBUG = settings_info["DEBUG"]

# AWS_CONN_INFO = {
#     'CLIENT_ID': settings_info['AWS']['CLIENT_ID'],
#     'CLIENT_SECRET': settings_info['AWS']['CLIENT_SECRET']
# }

ENV_NAME = settings_info['ENV']
if ENV_NAME == 'prod':
    pass
elif ENV_NAME == 'test':
    pass
else:
    pass

MONGO_URI = ''.join(['mongodb://',
                     settings_info["MONGODB"]["CLIENT_ID"], ':', settings_info["MONGODB"]["CLIENT_SECRET"],
                     '@', settings_info["MONGODB"]["HOSTS"][0], ':', settings_info["MONGODB"]["PORT"],
                     '/uvarc_unified_data'])
CELERY_BROKER_URL = MONGO_URI
CELERY_BACKEND_SETTINGS = {
    "options": {
        "authSource": "uvarc_unified_data",
    }
}
CELERY_BEAT_SCHEDULE = {
    'sync_ldap_data_task-interval': {
        'task': 'ldap_requests_sync_ldap_data_task',
        'schedule': timedelta(seconds=60)
    },
}
