from ldap3 import Server, Connection, ALL


class PrivateLDAPServiceHandler:
    def __init__(self, app):
        self.app = app
        self.private_ldap_url = f"ldap://{app.config["PRIVATE_LDAP_HOST"]}:{
            app.config["PRIVATE_LDAP_PORT"]}"
        self.private_ldap_bind_user = f"{
            app.config["PRIVATE_LDAP_CLIENT_ID"]}@{app.config["PRIVATE_LDAP_HOST"]}"
        self.private_ldap_bind_pass = app.config['PRIVATE_LDAP_CLIENT_SECRET']
        self.__private_ldap_attribute_list = [
            "sAMAccountName",
            "displayName",
            "department",
            "title",
            "pwdLastSet",
            "userAccountControl",
            "memberOf",
            "uidNumber",
            "primaryGroupID"
        ]
        self.__private_ldap_connection = None
        self.__private_ldap_connection = self.connect()

    def connect(self):
        """Create a connection to the specified LDAP server."""
        try:
            return Connection(
                Server(self.private_ldap_url, get_info=ALL, connect_timeout=10),
                user=self.private_ldap_bind_user,
                password=self.private_ldap_bind_pass, auto_bind=True,
                receive_timeout=60
            )
        except Exception as ex:
            self.app.logger.error(
                f"Error occured while connecting to private LDAP: {ex}")
            raise ex

    def close(self):
        if self.__private_ldap_connection:
            self.__private_ldap_connection.unbind()
    
    def __del__(self):
        self.close()
        self.__private_ldap_connection = None

    def get_private_ldap_info(self, uid):
        filter_string = f"(sAMAccountName={uid})"
        self.__private_ldap_connection.search(search_base="CN=Users,dc=eservices,dc=virginia,dc=edu", search_filter=filter_string,
                    search_scope="SUBTREE", attributes=self.__private_ldap_attribute_list)

        # Invalid uid
        if not self.__private_ldap_connection.entries:
            # self.app.logger.error(f"uid produced no values: {uid}")
            return None

        entries = self.__private_ldap_connection.entries

        # Should only be one entry
        entry = entries[0]

        ldap_dict_entry = entry.entry_attributes_as_dict

        # More readable sponsor entry
        sponsored = -1  # Initialize with a value that indicates "not found"
        for i, e in enumerate(ldap_dict_entry["memberOf"]):
            if "sponsored" in e:
                sponsored = i
                break
        if sponsored != -1:
            sponsor = ""
            for part in ldap_dict_entry["memberOf"]:
                sections = part.split(",")
                my_sec = sections[0]
                if "CN=UV" in my_sec:
                    sponsor += my_sec[6:] + " "
            ldap_dict_entry["Sponsored"] = "True [" + sponsor + "sponsored]"
        else:
            ldap_dict_entry["Sponsored"] = "False"

        # More readable User Account Control
        if ldap_dict_entry["userAccountControl"][0] == 512:
            ldap_dict_entry["userAccountControl"] = "enabled"
        elif ldap_dict_entry["userAccountControl"][0] == 514:
            ldap_dict_entry["userAccountControl"] = "disabled"
        elif ldap_dict_entry["userAccountControl"][0] == 8388608:
            ldap_dict_entry["userAccountControl"] = "password expired"

        pwd_last_set = ldap_dict_entry["pwdLastSet"][0]
        # Remove microseconds by setting them to 0
        pwd_last_set = pwd_last_set.replace(microsecond=0)
        # Convert to ISO format and replace '+00:00' with 'Z'
        iso_date_str = pwd_last_set.isoformat().replace('+00:00', 'Z')
        ldap_dict_entry["pwdLastSet"] = iso_date_str

        # Convert all list values to strings for easier insertion
        for key, value in ldap_dict_entry.items():
            if isinstance(value, list) and len(value) == 1:
                ldap_dict_entry[key] = value[0]
            if isinstance(value, list) and len(value) == 0:
                ldap_dict_entry[key] = ""

        # Convert Numbers to Strings
        ldap_dict_entry["primaryGroupID"] = str(
            ldap_dict_entry["primaryGroupID"])
        ldap_dict_entry["uidNumber"] = str(ldap_dict_entry["uidNumber"])
        # Add in school
        ldap_dict_entry = self.__add_school(ldap_dict_entry)

        return ldap_dict_entry

    def __add_school(self, response):
        department = response["department"]
        if department != None or department == "":
            school = department[0:2]
            if school.isupper():
                response["school"] = school
            else:
                if "Engineering" in department:
                    response["school"] = "EN"
                elif "Data Science" in department:
                    response["school"] = "DS"
                elif "Arts % Sciences" in department:
                    response["school"] = "AS"
                else:
                    response["school"] = "Others"
        else:
            response["school"] = ""
        return response


class PublicLDAPServiceHandler:
    def __init__(self, app):
        self.app = app
        self.public_ldap_url = f"ldap://{app.config["PUBLIC_LDAP_HOST"]}:{
            app.config["PUBLIC_LDAP_PORT"]}"
        self.__public_ldap_query_attribute_list = [
            "uid", "description", "uvaDisplayDepartment"]
        self.__public_ldap_conn = None
        self.__public_ldap_conn = self.__connect()

    def __connect(self):
        try:
            return Connection(
                    Server(
                        self.public_ldap_url,
                        get_info=ALL,
                        connect_timeout=10
                    ),
                    auto_bind=True
                )
        except Exception as ex:
            self.app.logger.error(
                f"Error occured while connecting to public LDAP: {ex}"
            )
            raise ex

    def close(self):
        if self.__public_ldap_conn:
            self.__public_ldap_conn.unbind()

    def __del__(self):
        self.close()
        self.__public_ldap_conn = None
    
    def get_public_ldap_query_attribute_list(self):
        return self.__public_ldap_query_attribute_list

    def get_public_ldap_info(self, uid):
        filter_string = f"(uid={uid})"
        self.__public_ldap_conn.search(
            search_base="ou=People,o=University of Virginia,c=US", 
            search_filter=filter_string,
            search_scope="SUBTREE", 
            attributes=self.__public_ldap_query_attribute_list
        )
        if not self.__public_ldap_conn.entries:
            return None

        entries = self.__public_ldap_conn.entries
        entry = entries[0]

        ldap_dict_entry = entry.entry_attributes_as_dict
        # Convert from list to string
        ldap_dict_entry["uid"] = ldap_dict_entry["uid"][0]
        return ldap_dict_entry
