import json
import logging
import os
from datetime import timedelta

NAME = 'UVARC UNIFIED SERVICE'
VERSION = '0.1'


def fetch_connections_info():
    if 'SETTINGS_JSON' in os.environ:
        settings = json.loads(os.environ['SETTINGS_JSON'])
        try:
            settings["JIRA"]['CLIENT_ID'] = os.environ['JIRA_CLIENT_ID']
            settings["JIRA"]['CLIENT_SECRET'] = os.environ['JIRA_CLIENT_SECRET']
            settings["SMTP"]['CLIENT_ID'] = os.environ['SMTP_CLIENT_ID']
            settings["SMTP"]['CLIENT_SECRET'] = os.environ['SMTP_CLIENT_SECRET']
            settings["AWS"]['CLIENT_ID'] = os.environ['AWS_CLIENT_ID']
            settings["AWS"]['CLIENT_SECRET'] = os.environ['AWS_CLIENT_SECRET']
            settings["MONGODB"]['CLIENT_ID'] = os.environ['MONGO_USER']
            settings["MONGODB"]['CLIENT_SECRET'] = os.environ['MONGO_PASSWORD']
            settings["LDAP_PUBLIC"]['CLIENT_ID'] = os.environ['LDAP_PUBLIC_CLIENT_ID']
            settings["LDAP_PUBLIC"]['CLIENT_SECRET'] = os.environ['LDAP_PUBLIC_CLIENT_SECRET']
            settings["LDAP_PRIVATE"]['CLIENT_ID'] = os.environ['LDAP_PRIVATE_CLIENT_ID']
            settings["LDAP_PRIVATE"]['CLIENT_SECRET'] = os.environ['LDAP_PRIVATE_CLIENT_SECRET']
            settings["HPC_API"]['CLIENT_ID'] = os.environ['HPC_API_CLIENT_ID']
            settings["HPC_API"]['CLIENT_SECRET'] = os.environ['HPC_API_CLIENT_SECRET']
        except Exception as ex:
            print('REQUIRED CREDENTIAL MISSING FROm THE ENV: {}'.format(str(ex)))
            raise ex
        return settings
    else:
        return json.load(open('./data/connections.json'))


def auth_callback_url_tuple(portal_host_url, auth_callback_route, auth_email_reset_route, auth_email_confirm_route): return (
    ''.join([portal_host_url, auth_callback_route]), ''.join([portal_host_url, auth_email_reset_route]), ''.join([portal_host_url, auth_email_confirm_route]))


settings_info = fetch_connections_info()
print(settings_info)

CORS_ENABLED = settings_info["CORS_ENABLED"]
DEBUG = settings_info["DEBUG"]

ESERVICES_LDAP_HOST = settings_info["LDAP_PRIVATE"]["HOSTS"][0]
ESERVICES_LDAP_PORT = settings_info["LDAP_PRIVATE"]["PORT"]
ESERVICES_LDAP_CLIENT_ID = settings_info["LDAP_PRIVATE"]["CLIENT_ID"]
ESERVICES_LDAP_CLIENT_SECRET = settings_info["LDAP_PRIVATE"]["CLIENT_SECRET"]

PUBLIC_LDAP_HOST = settings_info["LDAP_PUBLIC"]["HOSTS"][0]
PUBLIC_LDAP_PORT = settings_info["LDAP_PUBLIC"]["PORT"]

HPC_HOST = settings_info["HPC_API"]["HOSTS"][0]
HPC_CLIENT_SECRET = settings_info["HPC_API"]["CLIENT_SECRET"]

AWS_CONN_INFO = {
    'CLIENT_ID': settings_info['AWS']['CLIENT_ID'],
    'CLIENT_SECRET': settings_info['AWS']['CLIENT_SECRET']
}

ENV_NAME = settings_info['ENV']
if ENV_NAME == 'prod':
    CORS_ENABLED_ALLOWED_ORIGINS = ['https://rc.virginia.edu']
elif ENV_NAME == 'test':
    CORS_ENABLED_ALLOWED_ORIGINS = ['https://staging.rc.virginia.edu']
else:
    CORS_ENABLED_ALLOWED_ORIGINS = ['http://localhost:5000']

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
        'schedule': timedelta(seconds=10)
    },
}


ENV_BOOL_FLAGS_TUPLE = (ENV_NAME in (
    'local', 'dev'), ENV_NAME == 'prod')

DEVELOPMENT, PRODUCTION = ENV_BOOL_FLAGS_TUPLE

JIRA_CONN_INFO = {
    'HOST': settings_info['JIRA']['HOSTS'][0],
    'PORT': settings_info['JIRA']['PORT'],
    'CLIENT_ID': settings_info['JIRA']['CLIENT_ID'],
    'PASSWORD': settings_info['JIRA']['CLIENT_SECRET']
}

JIRA_PROJECTS = ('RIVANNA', 'IVY', 'GENERAL_SUPPORT',
                 'SENTINEL', 'CHASE', 'ACCORD_SUPPORT', 'UVA_RESEARCH_CONCIERGE_SERVICES')

JIRA_PROJECT_REQUEST_TYPES = (
    'RIVANNA_GET_IT_HELP',
    'IVY_GET_IT_HELP',
    'GENERAL_SUPPORT_TECHNICAL_SUPPORT',
    'SENTINEL_GET_IT_HELP',
    'CHASE_GET_IT_HELP',
    'ACCORD_SUPPORT_TECHNICAL_SUPPORT',
    'DATA_ANALYTICS_CONSULTING',
    'ITHRIV_CONCIERGE_INQUIRY',
)

JIRA_PROJECT_INFO_LOOKUP = {
    JIRA_PROJECTS[0]: 51,
    JIRA_PROJECTS[1]: 48,
    JIRA_PROJECTS[2]: 49,
    JIRA_PROJECTS[3]: 36,
    JIRA_PROJECTS[4]: 12,
    JIRA_PROJECTS[5]: 47,
}

JIRA_PROJECT_REQUEST_TYPE_LOOKUP = {
    JIRA_PROJECT_REQUEST_TYPES[0]: 413,
    JIRA_PROJECT_REQUEST_TYPES[1]: 397,
    JIRA_PROJECT_REQUEST_TYPES[2]: 402,
    JIRA_PROJECT_REQUEST_TYPES[3]: 291,
    JIRA_PROJECT_REQUEST_TYPES[4]: 106,
    JIRA_PROJECT_REQUEST_TYPES[5]: 387,
    JIRA_PROJECT_REQUEST_TYPES[6]: 401,
}

JIRA_CATEGORY_PROJECT_ROUTE_DICT = {
    'Rivanna Hpc': (JIRA_PROJECTS[0], JIRA_PROJECT_REQUEST_TYPES[0]),
    'Rivanna': (JIRA_PROJECTS[0], JIRA_PROJECT_REQUEST_TYPES[0]),
    'Ivy': (JIRA_PROJECTS[1], JIRA_PROJECT_REQUEST_TYPES[1]),
    'Software':
        (JIRA_PROJECTS[2], JIRA_PROJECT_REQUEST_TYPES[2]),
    'Storage': (JIRA_PROJECTS[2], JIRA_PROJECT_REQUEST_TYPES[2]),
    'Deans Allocation': (JIRA_PROJECTS[0], JIRA_PROJECT_REQUEST_TYPES[0]),
    'Consultation': (JIRA_PROJECTS[2], JIRA_PROJECT_REQUEST_TYPES[2]),
    'Other': (JIRA_PROJECTS[2], JIRA_PROJECT_REQUEST_TYPES[2]),
    'General': (JIRA_PROJECTS[2], JIRA_PROJECT_REQUEST_TYPES[2]),
    'Sentinel': (JIRA_PROJECTS[3], JIRA_PROJECT_REQUEST_TYPES[3]),
    'Chase': (JIRA_PROJECTS[2], JIRA_PROJECT_REQUEST_TYPES[2]),
    'Dcos': (JIRA_PROJECTS[2], JIRA_PROJECT_REQUEST_TYPES[2]),
    'Omero': (JIRA_PROJECTS[2], JIRA_PROJECT_REQUEST_TYPES[2]),
    'Skyline': (JIRA_PROJECTS[2], JIRA_PROJECT_REQUEST_TYPES[2]),
    'Accord Support': (JIRA_PROJECTS[5], JIRA_PROJECT_REQUEST_TYPES[5]),
    'Data Analytics': (JIRA_PROJECTS[2], JIRA_PROJECT_REQUEST_TYPES[6]),
    'Container': (JIRA_PROJECTS[2], JIRA_PROJECT_REQUEST_TYPES[2]),
}

# SMTP Email Settings
MAIL_SERVER = settings_info["SMTP"]["HOSTS"][0]
MAIL_PORT = settings_info["SMTP"]["PORT"]
MAIL_USERNAME = settings_info["SMTP"]["CLIENT_ID"]
MAIL_PASSWORD = settings_info["SMTP"]["CLIENT_SECRET"]
MAIL_USE_SSL = False
MAIL_USE_TLS = False
MAIL_TIMEOUT = 10
MAIL_SECRET_KEY = settings_info["SMTP"]["SECURE_KEY"]

if DEVELOPMENT:
    ALLOCATION_SPONSOR_EMAIL_LOOKUP = {
        'cas': 'rkc7h@virginia.edu',
        'seas': 'rkc7h@virginia.edu',
        'sds': 'rkc7h@virginia.edu',
        'hs': 'rkc7h@virginia.edu',
        'other': 'rkc7h@virginia.edu'
    }
    STORAGE_SPONSOR_EMAIL_LOOKUP = {
        'BII': ['rkc7h'],
        'DS': ['rkc7h', 'rkc7h']
    }

    KONAMI_ENPOINT_DEFAULT_SENDER = 'rkc7h@virginia.edu'
    KONAMI_ENPOINT_DEFAULT_RECEIVER = 'rkc7h@virginia.edu'

elif PRODUCTION:
    ALLOCATION_SPONSOR_EMAIL_LOOKUP = {
        'cas': 'lg8b@virginia.edu',
        'seas': 'wbk3a@virginia.edu',
        'sds': 'vsh@virginia.edu',
        'hs': 'jcm6t@virginia.edu',
        'other': 'nem2p@virginia.edu,rkc7h@virginia.edu'
    }
    STORAGE_SPONSOR_EMAIL_LOOKUP = {
        'BII': ['bii_rc_billing'],
        'DS': ['sds_rc']
    }
    KONAMI_ENPOINT_DEFAULT_SENDER = 'nem2p@virginia.edu'
    KONAMI_ENPOINT_DEFAULT_RECEIVER = 'nem2p@virginia.edu'
else:
    pass
