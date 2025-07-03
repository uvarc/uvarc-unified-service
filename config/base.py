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
            settings["WORKDAY"]['CLIENT_ID'] = os.environ['WORKDAY_CLIENT_ID']
            settings["WORKDAY"]['CLIENT_SECRET'] = os.environ['WORKDAY_CLIENT_SECRET']
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
            settings["QUALTRICS"]['CLIENT_ID'] = os.environ['QUALTRICS_CLIENT_ID'] if 'QUALTRICS_CLIENT_ID' in os.environ else None
            settings["QUALTRICS"]['CLIENT_SECRET'] = os.environ['QUALTRICS_CLIENT_SECRET'] if 'QUALTRICS_CLIENT_SECRET' in os.environ else None
            settings["LIBCAL"]['CLIENT_ID'] = os.environ['LIBCAL_CLIENT_ID'] if 'LIBCAL_CLIENT_ID' in os.environ else None
            settings["LIBCAL"]['CLIENT_SECRET'] = os.environ['LIBCAL_CLIENT_SECRET'] if 'LIBCAL_CLIENT_SECRET' in os.environ else None
            settings["HSL_API"]['CLIENT_ID'] = os.environ['HSL_API_CLIENT_ID'] if 'HSL_API_CLIENT_ID' in os.environ else None
            settings["HSL_API"]['CLIENT_SECRET'] = os.environ['HSL_API_CLIENT_SECRET'] if 'HSL_API_CLIENT_SECRET' in os.environ else None
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

PRIVATE_LDAP_HOST = settings_info["LDAP_PRIVATE"]["HOSTS"][0]
PRIVATE_LDAP_PORT = settings_info["LDAP_PRIVATE"]["PORT"]
PRIVATE_LDAP_CLIENT_ID = settings_info["LDAP_PRIVATE"]["CLIENT_ID"]
PRIVATE_LDAP_CLIENT_SECRET = settings_info["LDAP_PRIVATE"]["CLIENT_SECRET"]

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
    CORS_ENABLED_ALLOWED_ORIGINS = ['https://rc.virginia.edu', 'https://uvarc-api.pods.uvarc.io', 'https://usermeetings.pods.uvarc.io', 'https://uvarc-unified-service-prod.pods.uvarc.io']
elif ENV_NAME == 'test':
    CORS_ENABLED_ALLOWED_ORIGINS = ['https://staging.rc.virginia.edu', 'https://staging-onprem.rc.virginia.edu', 'https://uvarc-api.pods.uvarc.io', 'https://usermeetings.pods.uvarc.io', 'https://uvarc-unified-service-test.pods.uvarc.io']
else:
    CORS_ENABLED_ALLOWED_ORIGINS = ['http://localhost:5000', 'http://localhost:3000']

MONGO_URI = ''.join(['mongodb://',
                     settings_info["MONGODB"]["CLIENT_ID"], ':', settings_info["MONGODB"]["CLIENT_SECRET"],
                     '@', settings_info["MONGODB"]["HOSTS"][0], ':', settings_info["MONGODB"]["PORT"],
                     '/uvarc_unified_data_{env_name}'.format(env_name=ENV_NAME), '?retryWrites=true'])
CELERY_BROKER_URL = MONGO_URI
CELERY_BACKEND_SETTINGS = {
    "options": {
        "authSource": "uvarc_unified_data_{env_name}".format(env_name=ENV_NAME),
    }
}
CELERY_BEAT_SCHEDULE = {
    'sync_ldap_data_task-interval': {
        'task': 'ldap_requests_sync_ldap_data_task',
        'schedule': timedelta(minutes=30)
    },
    # 'version_groups_info_task-interval': {
    #     'task': 'version_groups_info_task',
    #     'schedule': timedelta(seconds=30)
    # }
}


ENV_BOOL_FLAGS_TUPLE = (ENV_NAME in (
    'local', 'dev', 'test'), ENV_NAME == 'prod')

DEVELOPMENT, PRODUCTION = ENV_BOOL_FLAGS_TUPLE

WORKDAY_CONN_INFO = {
    'HOST': settings_info['WORKDAY']['HOSTS'][0],
    'PORT': settings_info['WORKDAY']['PORT'],
    'CLIENT_ID': settings_info['WORKDAY']['CLIENT_ID'],
    'PASSWORD': settings_info['WORKDAY']['CLIENT_SECRET']
}

JIRA_CONN_INFO = {
    'HOST': settings_info['JIRA']['HOSTS'][0],
    'PORT': settings_info['JIRA']['PORT'],
    'CLIENT_ID': settings_info['JIRA']['CLIENT_ID'],
    'PASSWORD': settings_info['JIRA']['CLIENT_SECRET']
}

RC_SMALL_LOGO_URL = 'https://staging.rc.virginia.edu/images/logos/uva_rc_logo_full_340x129.png'

JIRA_PROJECTS = ('RIVANNA', 'IVY', 'GENERAL_SUPPORT',
                 'SENTINEL', 'CHASE', 'ACCORD_SUPPORT', 'UVA_RESEARCH_CONCIERGE_SERVICES','CONSULTATIONS & OUTREACH')

JIRA_PROJECT_REQUEST_TYPES = (
    'RIVANNA_GET_IT_HELP',
    'IVY_GET_IT_HELP',
    'GENERAL_SUPPORT_TECHNICAL_SUPPORT',
    'SENTINEL_GET_IT_HELP',
    'CHASE_GET_IT_HELP',
    'ACCORD_SUPPORT_TECHNICAL_SUPPORT',
    'DATA_ANALYTICS_CONSULTING',
    'ITHRIV_CONCIERGE_INQUIRY',
    'IT_HELP'
)

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

    JIRA_PROJECT_INFO_LOOKUP = {
        JIRA_PROJECTS[0]: 41,
        JIRA_PROJECTS[1]: 38,
        JIRA_PROJECTS[2]: 39,
        JIRA_PROJECTS[3]: 43,
        JIRA_PROJECTS[4]: 12,
        JIRA_PROJECTS[5]: 33,
        JIRA_PROJECTS[7]: 34
    }

    JIRA_PROJECT_REQUEST_TYPE_LOOKUP = {
        JIRA_PROJECT_REQUEST_TYPES[0]: 303,
        JIRA_PROJECT_REQUEST_TYPES[1]: 274,
        JIRA_PROJECT_REQUEST_TYPES[2]: 279,
        JIRA_PROJECT_REQUEST_TYPES[3]: 311,
        JIRA_PROJECT_REQUEST_TYPES[4]: 106,
        JIRA_PROJECT_REQUEST_TYPES[5]: 251,
        JIRA_PROJECT_REQUEST_TYPES[6]: 278,
        JIRA_PROJECT_REQUEST_TYPES[8]: 254
    }
    CUSTOMFIELD_VALUES = ('customfield_13076', 'customfield_13096', 'customfield_13090')

    JIRA_CUSTOM_FIELDS = {
        "custom_field_request_type": "customfield_13084",
        "custom_field_department": "customfield_13076",
        "custom_field_school": "customfield_13096",
        "custom_field_date": "customfield_13075",
        "custom_field_discipline": "customfield_13090",
        "custom_field_details": "customfield_13094",
        "custom_field_meeting_type": "customfield_13102",
        "custom_field_compute_platform": "customfield_13089",
        "custom_field_storage_platform": "customfield_13095"
    }

    QUEUE_NAME = 'uvarc_unified_response_queue_dev'

    STANDARD_STORAGE_REQUEST_INFO_TABLE = 'jira_standard_storage_requests_info_dev'
    PROJECT_STORAGE_REQUEST_INFO_TABLE = 'jira_project_storage_requests_info_dev'
    PAID_SU_REQUESTS_INFO_TABLE = 'jira_paid_su_requests_info_dev'

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

    JIRA_PROJECT_INFO_LOOKUP = {
        JIRA_PROJECTS[0]: 51,
        JIRA_PROJECTS[1]: 48,
        JIRA_PROJECTS[2]: 49,
        JIRA_PROJECTS[3]: 36,
        JIRA_PROJECTS[4]: 12,
        JIRA_PROJECTS[5]: 47,
        JIRA_PROJECTS[7]: 46
    }
    JIRA_PROJECT_REQUEST_TYPE_LOOKUP = {
        JIRA_PROJECT_REQUEST_TYPES[0]: 413,
        JIRA_PROJECT_REQUEST_TYPES[1]: 397,
        JIRA_PROJECT_REQUEST_TYPES[2]: 402,
        JIRA_PROJECT_REQUEST_TYPES[3]: 291,
        JIRA_PROJECT_REQUEST_TYPES[4]: 106,
        JIRA_PROJECT_REQUEST_TYPES[5]: 387,
        JIRA_PROJECT_REQUEST_TYPES[6]: 401,
        JIRA_PROJECT_REQUEST_TYPES[8]: 380
    }
    CUSTOMFIELD_VALUES = ('customfield_13176', 'customfield_13196', 'customfield_13190')
    JIRA_CUSTOM_FIELDS = {
        "custom_field_request_type": "customfield_13184",
        "custom_field_department": "customfield_13176",
        "custom_field_school": "customfield_13196",
        "custom_field_date": "customfield_13175",
        "custom_field_discipline": "customfield_13190",
        "custom_field_details": "customfield_13194",
        "custom_field_meeting_type": "customfield_13203",
        "custom_field_compute_platform": "customfield_13189",
        "custom_field_storage_platform": "customfield_13195"
    }

    QUEUE_NAME = 'uvarc_unified_response_queue'

    STANDARD_STORAGE_REQUEST_INFO_TABLE = 'jira_standard_storage_requests_info'
    PROJECT_STORAGE_REQUEST_INFO_TABLE = 'jira_project_storage_requests_info'
    PAID_SU_REQUESTS_INFO_TABLE = 'jira_paid_su_requests_info'

    KONAMI_ENPOINT_DEFAULT_SENDER = 'nem2p@virginia.edu'
    KONAMI_ENPOINT_DEFAULT_RECEIVER = 'nem2p@virginia.edu'
else:
    pass
