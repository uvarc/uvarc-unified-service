
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import pandas as pd
from datetime import datetime, timezone

# MongoDB connection parameters
MONGO_HOST = "localhost" 
MONGO_PORT = 27017
MONGO_USER = "root"
MONGO_PASS = "example"
MONGO_DB = "admin"

# Connect to MongoDB
client = MongoClient(
    host=MONGO_HOST,
    port=MONGO_PORT,
    username=MONGO_USER,
    password=MONGO_PASS,
    authSource=MONGO_DB
)

# Initialize the database 
db = client['uvarc_unified_data']
users = db['users']

# Read CSV File
df = pd.read_csv("data/ldap_files/all_users_formatted_to_ldap.csv")

# convert to datatime object
df["date_of_query"] = pd.to_datetime(df["date_of_query"])

# Convert NaN entries to empty strings
df = df.fillna('')

#Insert uid 
df.insert(loc=0, column="uid", value=df["UserID"])

# Replace Lastname and Firstname w/ displayName
df.insert(loc=1, column="displayName", value=(df["Lastname"] + ", " + df["Firstname"] + " (" + df["uid"] + ")"))
df.drop(columns=["Lastname","Firstname"], inplace=True)

# Fill out department 
def extract_department(affiliation):
    if ':' in affiliation:
        return affiliation.split(':')[1]
    return affiliation

df["department"] = df["affiliation"].apply(extract_department)
# Create uvaDisplayDepartment attribute [in current ldap info -> might be list] and drop affiliation
df.insert(loc=4, column="uvaDisplayDepartment", value=(df["affiliation"]))
df.drop(columns="affiliation", inplace=True)



# Create a dictionary to hold user data
user_data = {}
# Create set of names
uids = set()

# Iterate over rows
for index, row in df.iterrows():
    user_id = row["UserID"]
    uids.add(user_id)
    query = row.drop(labels="UserID").to_dict()  # Convert the row to a dictionary and drop 'UserID'
    
    if user_id in user_data:
        if query["date_of_query"] > user_data[user_id]["recent_ldap_info"]["date_of_query"]:
            user_data[user_id]["ldap_info_log"].append(user_data[user_id]["recent_ldap_info"])
            user_data[user_id]["recent_ldap_info"] = query
        else:
            user_data[user_id]["ldap_info_log"].append(query)
    else:
        user_data[user_id] = {"recent_ldap_info": query, "ldap_info_log": []}

# UTC data w/ timestamp
current_timestamp = datetime.now(timezone.utc)

# Convert user_data for Mongo Insertion
records = [{"UserID": user_id, "recent_ldap_info" : queries["recent_ldap_info"], "ldap_info_log": queries["ldap_info_log"],"date_modified": current_timestamp, "comments_on_changes": "Initial Entry"} for user_id, queries in user_data.items()]

# Insert records into the MongoDB collection
users.insert_many(records)

client.close()

print("Database initialization complete")