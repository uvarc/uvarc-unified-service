import ast
import datetime
import pandas as pd
from app import app
from common_service_handlers.libcal_service_handler import LibcalServiceHandler
from common_service_handlers.qualtrics_service_handler import QualtricsServiceHandler
from common_utils.business import UVARCUserInfoManager
import logging
import re

class UVARCWorkshopVisualizationDataManager:
    def __init__(self):
        pass
    
    def get_workshop_data(self, begin='2024-01-01'):
        libcal = LibcalServiceHandler(app)
        start, end, days = libcal.timeframe(begin, datetime.datetime.now().strftime("%Y-%m-%d"))
        libcal_df = libcal.get_RCeventsforAllTimes(
            cal_type="libcal",
            start=start,
            days=days,
        )

        hsl_df = libcal.get_RCeventsforAllTimes(
            cal_type="hsl",
            start=start,
            days=days,
        )

        combined_df = pd.concat([libcal_df, hsl_df], ignore_index=True)

        # filter out duplicate workshops
        combined_df = combined_df.drop_duplicates(subset='id')

        return combined_df
    
    def get_attendance_data(self, begin='2024-01-01'):
        libcal = LibcalServiceHandler(app)
        start, end, days = libcal.timeframe(begin, datetime.datetime.now().strftime("%Y-%m-%d"))
        evt_fields = ["id", "title", "description","start", "end", "presenter"]
        fields = libcal.unique_ordered([], evt_fields, libcal.registration_fields)
        
        libcal_df = libcal.get_RCeventsforAllTimes(
            cal_type="libcal",
            start=start,
            days=days,
            fields=fields,
        )

        hsl_df = libcal.get_RCeventsforAllTimes(
            cal_type="hsl",
            start=start,
            days=days,
            fields=fields,
        )
        
        combined_df = pd.concat([libcal_df, hsl_df], ignore_index=True)

        event_ids = list(zip(combined_df["id"].values, combined_df["cal_type"].values))

        # DataFrame with registrations, optional: filter by user
        reg_df = libcal.get_multiple_registrations(event_ids)

        all_uids = reg_df['uid'].unique()
        ldap_helper = UVARCUserInfoManager()

        logging.info(f"Fetching LDAP info for {len(all_uids)} unique UIDs")

        ldap_info = [ldap_helper.get_user_info(uid) for uid in all_uids]
        ldap_info = [{
            'department': info['department'],
            'school': info['school'],
            'uid': info['uid']
        } for info in ldap_info if info is not None]

        logging.info(f"Fetched LDAP info for {len(ldap_info)} UIDs")

        # add department and school info to reg_df
        ldap_df = pd.DataFrame(ldap_info)
        reg_df = pd.merge(reg_df, ldap_df, left_on='uid', right_on='uid', how='left', copy=False)

        # convert NaN to empty string
        reg_df['department'] = reg_df['department'].fillna('')
        reg_df['school'] = reg_df['school'].fillna('')

        non_numeric_df = libcal.non_numeric(combined_df)
        reg_df = pd.merge(reg_df, non_numeric_df, left_on="event_id", right_on="id", how="inner", copy=False)

        # strip idenifiers from reg_df
        identifiers = ['first_name', 'last_name', 'email', 'uid']
        reg_df = reg_df.drop(columns=identifiers, axis=1, inplace=False)

        logging.info(f"Final attendance DataFrame length: {len(reg_df)}")

        return reg_df

    def merge_workshop_attendance_data(self, workshop_data, attendance_data):
        workshop_data = workshop_data[workshop_data['start'] >= '2024-01-01']

        # add list of registrations to each workshop
        workshop_data['registrations'] = workshop_data['id'].apply(lambda x: attendance_data[attendance_data['id'] == x].to_dict(orient='records'))
        workshop_data['attendees'] = workshop_data['registrations'].apply(lambda x: [y for y in x if y['attendance'] == 1])
        workshop_data['attendance'] = workshop_data['attendees'].apply(lambda x: len(x))

        # sort by start date
        workshop_data = workshop_data.sort_values(by='start')

        # remove column for status and cal_type
        workshop_data = workshop_data.drop(columns=['has_registration_opened', 'has_registration_closed', 'status', 'cal_type', 'online_join_url', 'online_join_password', 'registration', 'wait_list', 'online_meeting_id'], errors='ignore')

        # create tags manually
        tags = {
            'Python': ['python', 'pandas', 'numpy', 'scipy', 'matplotlib'],
            'Matlab': ['matlab'],
            'SQL': ['sql'],
            'Deep Learning': ['deep learning'],
            'Machine Learning': ['machine learning', 'deep learning', 'scikit-learn', 'tensorflow', 'keras'],
            'Containers': ['docker', 'kubernetes', 'container'],
            'Slurm': ['slurm'],
            'CLI': ['command line', 'cli', 'shell scripting'],
            'HPC Core': ['11890719', '11890924', '12423016', '12423080', '12889799', '13832854', '13838434', '14584244', '14584667'],
            'Bioinformatics': ['bioinformatics', 'drug discovery'],
        }

        # add tags to data based on title and description
        workshop_data['tags'] = workshop_data['description'].str.split('Prerequisites:').str[0]
        workshop_data['tags'] = workshop_data['title'].str.lower() + ' ' + workshop_data['tags'].str.lower() + ' ' + workshop_data['id'].astype(str)
        workshop_data['tags'] = workshop_data['tags'].apply(lambda x: [tag for tag, keywords in tags.items() if any(keyword in x for keyword in keywords)])

        workshop_data['category'] = workshop_data['category'].apply(lambda x: [y['name'] for y in ast.literal_eval(str(x))])
        workshop_data['category'] = workshop_data['category'].apply(lambda x: [y for y in x if y not in set(['Data Workshop > Research Computing Data Workshop', 'Data Workshop', 'Workshop'])])

        workshop_data['tags'] = list(workshop_data['tags'] + workshop_data['category'])

        return workshop_data.to_dict(orient='records')
    
class UVARCWorkshopSurveyDataManager:
    def __init__(self, survey_id):
        self.survey_id = survey_id

    def get_workshop_survey_data(self):
        qualtrics = QualtricsServiceHandler(app)
        try:
            survey_data, _, _ = qualtrics.get_survey(self.survey_id)
        except Exception as e:
            raise Exception(f"Error retrieving workshop survey data: {str(e)}") from e
        
        survey_data['survey_id'] = self.survey_id

        # strip identifiers from survey data
        identifiers = ['StartDate', 'EndDate', 'Status', 'IPAddress', 'RecipientEmail', 'RecipientFirstName', 'RecipientLastName', 'ExternalReference', 'LocationLatitude', 'LocationLongitude', 'DistributionChannel', 'UserLanguage']
        survey_data = survey_data.drop(columns=identifiers, axis=1, inplace=False)

        survey_data = survey_data.fillna('')
        
        # account for "Other" values
        survey_data['Q1'] = survey_data.apply(
            lambda row: row['Q1A'] if row['Q1'] == 'Other' and row['Q1A'] else row['Q1'], axis=1
        )


        survey_data['Q2'] = survey_data.apply(
            lambda row: row['Q2A'] if row['Q2'] == 'Other' and row['Q2A'] else row['Q2'], axis=1
        )

        # if any Q2 column contains substring "OGPA", replace it with "OGPA"
        survey_data['Q2'] = survey_data['Q2'].apply(lambda x: 'OGPA' if 'OGPA' in x else x)
        # convert "Office of Graduate and Postdoctoral Affairs" to "OGPA" in Q2
        survey_data['Q2'] = survey_data['Q2'].replace({ 'Office of Graduate and Postdoctoral Affairs': 'OGPA' })

        survey_data = survey_data.drop(columns=['Q1A', 'Q2A'], axis=1, inplace=False)

        # convert Q3 to a list of topics
        survey_data['Q3'] = survey_data['Q3'].apply(
            lambda x: [y for y in re.split(r',(?!\s)', x) if y.strip()]
        )

        return survey_data.to_dict(orient='records')
