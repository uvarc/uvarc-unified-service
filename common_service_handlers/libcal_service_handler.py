"""
Created on Wed Jan  3 20:49:13 2024

@author: khs3z
"""
import re
import logging
import os
import pandas as pd
import requests
# import utils
from datetime import datetime, timedelta
import calendar

# List of Valid RC Presenters
presenters = [
    "Jackie Huband",
    "Jacalyn Huband",
    "Karsten Siller"
    "Marcus Bobar",
    "Gladys Andino",
    "Christina Gancayco",
    "Caitlin Jagla",
    "Will Rosenow",
    "Ed Hall",
    "Ahmad Sheikhzada",
    "Ruoshi Sun",
    "Paul Orndorff",
    "Katherine Holcomb",
    "Kathryn Linehan",
    "Angela Boakye Danquah",
    "Priyanka Prakash",
    "Pri Prakash",
    "Alois D’Uston de Villereglan",
    "Hana Parece",
    "Camden Duy",
    "Deb Triant"
]


event_fields = [
    "id",
    "title",
    # "allday",
    "start",
    "end",
    "description",
    "category",
    "url",
    "location",
    "presenter",
    "seats",
    "registration",
    "has_registration_opened",
    "has_registration_closed",
    # "physical_seats",
    # "physical_seats_taken",
    # "online_seats",
    # "online_seats_taken",
    "seats_taken",
    "wait_list",
    # "geolocation",
    # "future_dates",
    # "registration_cost",
    # "more_info",
    # "setup_time",
    # "teardown_time",
    # "online_user_id",
    # "zoom_email",
    "online_meeting_id",
    # "online_host_url",
    "online_join_url",
    "online_join_password",
    # "online_provider",
    "status",
    "cal_type"
]


class LibcalServiceHandler:
    def __init__(self, app):
        self.app = app
        self.libcal_url = self.__get_host_info("LIBCAL_CONN_INFO")
        self.hsl_url = self.__get_host_info("HSL_API_CONN_INFO")
        self.libcal_category_id = app.config["LIBCAL_CATEGORY_ID"]
        self.general_category_id = app.config["GENERAL_CATEGORY_ID"]
        self.hsl_category_id = app.config["HSL_CATEGORY_ID"]
        self.hsl_cal_id = app.config["HSL_CAL_ID"]
        self.rds_cal_id = app.config["RDS_CAL_ID"]
        self.registration_fields = [
            "booking_id",
            # "registration_type",
            "first_name",
            "last_name",
            # "barcode",
            # "phone",
            "email",
            "registered_date",
            "attendance",
        ]

        self.refresh_tokens()

    def __get_host_info(self, info_field):
        return 'https://{}:{}/1.1/'.format(
            self.app.config[info_field]["HOST"],
            self.app.config[info_field]["PORT"]
        )
    
    def refresh_tokens(self):
        client_ids = {
            "libcal": self.app.config["LIBCAL_CONN_INFO"]["CLIENT_ID"],
            "hsl": self.app.config["HSL_API_CONN_INFO"]["CLIENT_ID"]
        }

        client_secrets = {
            "libcal": self.app.config["LIBCAL_CONN_INFO"]["PASSWORD"],
            "hsl": self.app.config["HSL_API_CONN_INFO"]["PASSWORD"]
        }

        self.libcal_token = self.get_token(
            client_ids["libcal"],
            client_secrets["libcal"],
            "libcal"
        )

        self.hsl_token = self.get_token(
            client_ids["hsl"],
            client_secrets["hsl"],
            "hsl"
        )
    
    def remove_html(self, raw_html):
        CLEANR = re.compile('<.*?>|\n|\r|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')

        if type(raw_html) == str:
            return re.sub(CLEANR, '', raw_html)
        else:
            return raw_html

    def get_url(self, cal_type):
        urls = {
            "libcal": self.libcal_url,
            "hsl": self.hsl_url
        }
        return urls.get(cal_type, self.libcal_url)

    def get_token(self, client_id, client_secret, cal_type):
        url = self.get_url(cal_type)
        
        payload = {
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "client_credentials",
        }
        full_url = f"{url}oauth/token"
        r = requests.post(full_url, data=payload)
        return r.json().get("access_token")

    def get_headers(self, cal_type):
        tokens = {
            "libcal": self.libcal_token,
            "hsl": self.hsl_token
        }
        return { 'Authorization': f"Bearer {tokens.get(cal_type, self.libcal_token)}",
                 'Content-Type': 'application/json',
                 'Accept': 'application/json' }

    def timeframe(self, begin, end, daylimit=365):
        if begin == "0000-00-00":
            begintime = datetime.now()
            endtime = datetime.now() + timedelta(days=365)
            days = daylimit
        else:
            if begin is None or "":
                begintime = datetime.now()
            else:
                begintime = datetime.strptime(begin, "%Y-%m-%d")
            if end is None or "":
                endtime = datetime.now()
            else:
                endtime = datetime.strptime(end, "%Y-%m-%d")
            days = (endtime - begintime).days

        
        # if days > daylimit:
        #     days = daylimit
        #     endtime = begintime + timedelta(days=days)
        beginstr = begintime.strftime("%Y-%m-%d")
        endstr = endtime.strftime("%Y-%m-%d")
        return beginstr, endstr, days


    def get_calendar_ids(self, cal_type):
        url = self.get_url(cal_type)
        headers = self.get_headers(cal_type)
        r = requests.get(f"{url}calendars", headers=headers)
        logging.debug(r.url)
        cals = r.json().get("calendars")
        ids = [int(item.get("calid")) for item in cals]
        return ids


    def search_events(self, cal_type, searchstr, start=None, limit=500):
        url = self.get_url(cal_type)
        headers = self.get_headers(cal_type)
        payload = {
            "search": searchstr,
            "date": start,
            "limit": limit,
        }
        if self.libcal_category_id is not None:
            payload["category"] = (self.libcal_category_id,)
        if self.rds_cal_id is not None:
            payload["cal_id"] = self.rds_cal_id
        r = requests.get(f"{url}event_search", headers=headers, params=payload)
        logging.debug(r.url)
        events = r.json().get("events")
        for chunk in events:
            cat = chunk.get("category")
            logging.debug(chunk.get("title"))
        return events


    def get_event(self, event_id, cal_type):
        url = self.get_url(cal_type)
        headers = self.get_headers(cal_type)
        payload = {}
        r = requests.get(f"{url}event/{event_id}", headers=headers, params=payload)
        logging.debug(r.url)
        event = r.json()
        return event
    
    def get_RCeventsforAllTimes(
        self,
        cal_type,
        start=None,
        days=365,
        limit=500,
        event_ids=None,
        fields=event_fields,
    ):
        url = self.get_url(cal_type)
        headers = self.get_headers(cal_type)
        payload = {
            "cal_id": self.rds_cal_id if cal_type == "libcal" else self.hsl_cal_id,
            "category": self.general_category_id if cal_type == "libcal" else self.hsl_category_id,
            "days": days,
            "limit": limit,
        }
        # Relevant ID to decrease search time 
        if(cal_type == "hsl"):
            del payload["category"]

        if start != "0000-00-00":
            payload["date"] = start
        # Create empty dataframe
        event_df = pd.DataFrame({}, columns=fields)

        # Number of API Requests as limit is 365 days
        # Adds 1 to account for API Requests for leftover days (not full years)
        numberOfIterations = days // 365 + 1

        # Convert string back into DateTime Object for 
        beginstrTime = datetime.strptime(start, "%Y-%m-%d")

        # Determine number of days in year for current year
        daysInYear = 365 + calendar.isleap(beginstrTime.year)
        
        for x in range(numberOfIterations):
            # Instead of priming read, we run directly into the loop so this will account for the leftover days 
            if days < 0:
                days = days + daysInYear 
            
            beginstrTime = datetime.strptime(start, "%Y-%m-%d")    
            daysInYear = 365 + calendar.isleap(beginstrTime.year)
            
            payload["date"] = start
            payload["days"] = days
            
            if not event_ids or len(event_ids) == 0:
                r = requests.get(f"{url}events", headers=headers, params=payload)
            else:
                r = requests.get(
                    f"{url}events/{','.join(event_ids)}", headers=headers, params=payload
            )
            logging.debug(r.url)
            events = r.json().get("events")
            
            if len(events) > 0:
                # filter, flatten dict and remove any html tags from list of dict
                new_df = self.to_dataframe(events, fields)
                # filter the dataframe for RC presenters and by tag 
                new_df = new_df[new_df['presenter'].str.contains('|'.join(presenters))]
                # Standardize Jackie's Name
                new_df = self.standardizeName(new_df, "Jacalyn Huband", "Jackie Huband")
                # Standardize Pri's Name
                new_df = self.standardizeName(new_df, "Priyanka Prakash", "Pri Prakash")
                # Standardize Gladys's Name
                new_df = self.standardizeName(new_df, "Glady Andino", "Gladys Andino Bautista")
                # appends the status column to identify cancellations
                new_df = self.createStatus(new_df)
                # appends the cal_type column, so we know which entry came from which data set
                new_df = self.createCalType(new_df, cal_type)
                #remove duplicates [Cross-Listing between HSL & RDS
                new_df = self.removeDuplicates(new_df)
                logging.info(f"{len(new_df)} events found.")
            else:
                logging.info("No events found.")
            # Concatenate existing dataframe with the new dataframe for this iteration
            if len(events) > 0:
                if event_df.empty:
                    event_df = new_df
                else:
                    event_df = pd.concat([event_df, new_df])
            # Update start and days for next API Request (if necessary) or break out of the loop 
            # as the number of iterations have passed
            start = (beginstrTime + timedelta(daysInYear)).strftime("%Y-%m-%d")
            days = days - daysInYear
        return event_df

    def get_event_registrations(self, event_id, cal_type, fields=None):
        headers = self.get_headers(cal_type)
        url = self.get_url(cal_type)
        r = requests.get(f"{url}events/{event_id}/registrations?waitlist=1", headers=headers)
        logging.debug(r.url)
        registrants = [item.get("registrants") for item in r.json()]
        # Figures out Waitlist participants 
        waitlist = [item.get("waitlist") for item in r.json()]
        # Combine
        registrants = registrants + waitlist
        # flatten list of list
        registrants = [r for entry in registrants for r in entry]
        if fields is not None:
            # filter to include only specified fields
            registrants = [{k: v for k, v in r.items() if k in fields} for r in registrants]
        return registrants


    def _split_uid(self, email):
        if "@virginia.edu" in email:
            uid = email.split("@")[0]
            return uid
        else:
            return email


    def _to_boolean(self, df, column):
        boolean_map = {"True": 1, "False": 0, "yes": 1, "-": 0}
        if column in df.columns.values:
            df[column] = df[column].map(boolean_map).fillna(0).astype(int)
        return df


    def to_dataframe(self, items, fields=None, constants={}, dtype={}, sep="."):
        if len(items) > 0:
            logging.debug(f"items keys={items[0].keys()}")
            l_constants = {k: len(items) * [v] for k, v in constants.items()}
            c_df = pd.DataFrame.from_dict(l_constants)
            df = pd.json_normalize(items, sep=sep).map(self.remove_html)
            if fields:
                fields = [f for f in fields if f in df.columns.values]
                logging.debug(f"Available Columns: {df.columns.values}")
                df = df[fields]
            combined_df = pd.concat([c_df, df], axis=1)
            logging.debug(f"Columns after filtering: {df.columns.values}")
            return combined_df
        else:
            fields = fields if fields is not None else []
            return pd.DataFrame(columns=list(constants.keys()) + fields, dtype="int64")


    def get_multiple_registrations(self, event_ids):
        dfs = []
        for event_id, cal_type in event_ids:
            registrations = self.get_event_registrations(event_id=event_id, cal_type=cal_type)
            df = self.to_dataframe(
                registrations, constants={"event_id": event_id, "registrations": 1}
            )
            # df = _to_boolean(df, "registration")
            df = self._to_boolean(df, "attendance")
            
            if "email" in df.columns.values:
                df["uid"] = df["email"].apply(self._split_uid)
            
            # df["cal_type"] = cal_type
            dfs.append(df)
            #  logging.info(f"Event {event_id}, {df.columns.values}, Registrations: {len(df)}")
        if len(dfs) == 0:
            logging.info("No events found.")
            return None
        else:
            return pd.concat(dfs, axis=0)
        
    #determines whether a workshop is cancelled or scheduled
    def determine_status(self, title):
        if 'Cancelled' in title:
            return 'cancelled'
        if 'CANCELED' in title:
            return 'cancelled'
        
        return 'scheduled'

    #creates status column based off of cancellation info 
    def createStatus(self, df):
        df['status'] = df['title'].apply(self.determine_status)
        return df

    def createCalType(self, df, cal_type):
        df['cal_type'] = cal_type
        return df

    # Standardize name for easy filtering
    def standardizeName(self, df, formalName, prefName):
        delimiters = [' & ', ', ']

        def reformat_name(name):
            return formalName if prefName in name else name

        df['presenter'] = df['presenter'].apply(lambda x: ', '.join([reformat_name(name) for part in x.split(', ') for name in part.split(' & ')]))
        
        return df

    # Remove Duplicates to prevent counting workshops that were submitted to both HSL and RDS(Libcal)
    def removeDuplicates(self, df):
        if 'description' in df.columns: 
            filtered_df = df[~df['description'].str.contains("cross-listing", case=False, na=False)]
            return filtered_df
        return df

    # Returns all calendar Ids associated with a specific calendar
    def get_calendars(self, cal_type):
        url = self.get_url(cal_type)
        headers = self.get_headers(cal_type)
        payload = {}
        r = requests.get(f"{url}calendars", headers=headers, params=payload)
        return r.json()

    # Returns all categories [won't work as we do not have permissions]
    def get_categories(self, cal_type):
        url = self.get_url(cal_type)
        headers = self.get_headers(cal_type)
        payload = {}
        r = requests.get(f"{url}categories", headers=headers, params=payload)
        return r.json()


    def format(self, df, fields):
        existing_fields = [f for f in fields if f in df.columns.values]
        return df[existing_fields]


    def summarize(self, df, groups=["event_id"], fields=None, sort=False):
        groups = [g for g in groups if g in df.columns.values]
        if fields is None:
            fields = list(df.columns.values)
        else:
            fields = [f for f in fields if f in df.columns.values]
        logging.debug(f"Columns found: {df.columns.values}.")
        logging.debug(f"Grouping by {groups}, aggregating fields={fields}.")
        summary = df[groups + fields].groupby(groups).sum().reset_index()
        if sort:
            summary = summary.sort_values(groups)
        return summary


    def save_dataframe(self, df, output, append=False, overwrite=False, deduplicate=True):
        fileexists = os.path.exists(output)
        if fileexists and not append:
            if not overwrite:
                logging.info(
                    f"Output file {output} exists. Overwrite is disabled. New data is not saved. If you wish to overwrite {output}, please include --overwrite."
                )
                return
            else:
                logging.info(f"Overwriting {output}.")
        if fileexists and append:
            logging.info(f"Appending existing {output}.")
            old_df = pd.read_csv(output)
            df = pd.concat([old_df, df], axis=0)
            #if deduplicate:
                #l_df = len(df)
                # df = df.drop_duplicates(keep="last")
                # logging.info(f"Dropping {l_df-len(df)} duplicates")
        df.to_csv(output, index=False)
        logging.info(f"{output} saved.")


    def numeric_columns(self, df, exclude=["event_id", "id", "booking_id"]):
        num_cols = [c for c in df.select_dtypes(include='number').columns.values if c not in exclude]
        return num_cols

    def non_numeric(self, df, include=["event_id", "id", "booking_id"]):
        include = [i for i in include if i in df.columns.values]
        non_num_cols = [c for c in set(list(df.select_dtypes(exclude='number').columns.values) + include)]
        return df[non_num_cols]

    def unique_ordered(self, *lists):
        logging.debug(lists)
        combined = list(lists[0]) # make copy to avoid side effect
        for l in lists[1:]:
            combined.extend([i for i in l if i not in combined])
        logging.debug (f"lists in {lists}")
        logging.debug (f"combined out {combined}")
        return combined 
