db = db.getSiblingDB("uvarc_unified_data");
db.createUser({
  user: "uvarc_unified_db_user",
  pwd: "uvarc_unified_db_pass", // or cleartext password
  roles: [{ role: "readWrite", db: "uvarc_unified_data" }],
});
db.createCollection('users');
