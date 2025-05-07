db = db.getSiblingDB("uvarc_unified_data_local");
db.createUser({
  user: "uvarc_unified_db_user_local",
  pwd: "uvarc_unified_db_pass", // or cleartext password
  roles: [{ role: "dbOwner", db: "uvarc_unified_data_local" }],
});

db.createCollection('uvarc_users');
// db.createCollection('uvarc_users', {
//   validator: {
//     $jsonSchema: {
//       bsonType: "object",
//       required: ["uis","update_time"],
//       properties: {
//         uid: {
//           bsonType: "String",
//           description: "must be a valid email address and is required"
//         },
//         update_time:{
//           bsonType: "Date",
//           description: "must contain a valid project update date"
//         }
//       }
//     }
//   }
// });
// db.createCollection('uvarc_groups', {
//   validator: {
//     $jsonSchema: {
//       bsonType: "object",
//       required: ["group_name","group_members_update_time"],
//       properties: {
//         group_name: {
//           bsonType: "String",
//           description: "must be a valid email address and is required"
//         },
//         group_members_update_time:{
//           bsonType: "Date",
//           description: "must contain a valid project update date"
//         }
//       }
//     }
//   }
// });



// // db.users.drop();
// // db.admins.drop();
// // db.projects.drop();
// db.createCollection('users', {
//   validator: {
//     $jsonSchema: {
//       bsonType: "object",
//       required: ["email","first_name","last_name","user_create_date"],
//       properties: {
//         email: {
//           bsonType: "string",
//           pattern: "^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$",
//           description: "must be a valid email address and is required"
//         },
//         first_name:{
//           bsonType: "string",
//           description: "must contain a valid user first name"
//         },
//         last_name:{
//           bsonType: "string",
//           description: "must contain a valid user last name"
//         },
//         phone:{
//           bsonType: "string",
//           description: "must contain a valid user phone number"
//         },
//         user_create_date:{
//           bsonType: "string",
//           description: "must contain a valid project create date"
//         },
//         user_update_date:{
//           bsonType: "string",
//           description: "must contain a valid project update date"
//         },
//         user_update_by_user_id:{
//           bsonType: "ObjectId",
//           description: "must contain a valid user id from users collection"
//         },
//       }
//     }
//   }
// });
// db.users.createIndex({ "email": 1 }, { unique: true });
// db.runCommand( {
//   collMod: "users",
//   validationLevel: "strict",
//   validationAction: "error"
// })
// db.createCollection('admins', {
//   validator: {
//     $jsonSchema: {
//       bsonType: "object",
//       required: ["user_id","admin_permissions"],
//       properties: {
//         user_id:{
//           bsonType: "ObjectId",
//           description: "must contain a valid admin user id"
//         },
//         admin_permissions: {
//           bsonType: "array",
//           minItems: 1,
//           required: ["admin_role"],
//           properties: {
//             admin_role: {
//               enum: [ "app-admin", "app-approver"],
//               description: "must be a valid  admin role and is required"
//             },
//           }
//         }
//       }
//     }
//   }
// });
// db.admins.createIndex({ "user_id": 1 }, { unique: false });
// db.runCommand( {
//   collMod: "admins",
//   validationLevel: "strict",
//   validationAction: "error"
// })
// db.createCollection('projects', {
//   validator: {
//     $jsonSchema: {
//       bsonType: "object",
//       required: ["project_name","project_desc", "project_create_date", "project_update_by_user_id", "project_status", "data_sensitivity", "approval_status", "project_permissions"],
//       properties: {
//         project_name:{
//           bsonType: "string",
//           description: "must contain a valid project name"
//         },
//         project_desc:{
//           bsonType: "string",
//           description: "must contain a valid project description"
//         },
//         project_create_date:{
//           bsonType: "string",
//           description: "must contain a valid project create date"
//         },
//         project_update_date:{
//           bsonType: "string",
//           description: "must contain a valid project update date"
//         },
//         project_update_by_user_id:{
//           bsonType: "string",
//           description: "must contain a valid user id from users collection"
//         },
//         project_status:{
//           enum: [ "Active", "Provisioned", "Archived" ],
//           description: "can only be one of the enum values and is required"
//         },
//         data_sensitivity:{
//           enum: [ "HIPPA", "FERPA", "Other" ],
//           description: "must be a  HIPPA, FERPA or Other data sensitivity indicator"
//         },
//         other_sensitivity_desc:{
//           bsonType: "string",
//           description: "OTHER data sensitivity description"
//         },
//         approval_status:{
//           enum: [ "Approved", "Denied", "Pending Approval" ],
//           description: "can only be one of the enum values and is required"
//         },
//         approved_by_user_id:{
//           bsonType: "string",
//           pattern: "^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$",
//           description: "must be a valid email address and is required"
//         },
//         approved_date:{
//           bsonType: "string",
//           description: "project approved date"
//         },
//         project_permissions: {
//           bsonType: "array",
//           minItems: 1,
//           required: ["user_id", "user_role", "is_pi"],
//           properties: {
//             user_id:{
//               bsonType: "ObjectId",
//               description: "must contain a valid user id from users collection"
//             },
//             user_role: {
//               bsonType: "string",
//               description: "must be a valid user role (project-admin, project-user) and is required"
//             },
//             is_pi: {
//               bsonType: "Boolean",
//               description: "must be a true or false indicating member is PI or not"
//             },
//           },
//           dependencies: {
//             "user_id": ["user_role"],
//             "user_role": ["user_id"]
//           }
//         }
//       }
//     }
//   }
// });
// db.projects.createIndex({ "user_permissions.user_id": 1 }, { unique: false });
// db.projects.createIndex({ "user_permissions.user_role": 1 }, { unique: false });
// db.projects.createIndex({ "user_permissions.user_id": 1, "user_permissions.user_role": 1 }, { unique: false });
// db.runCommand( {
//   collMod: "projects",
//   validationLevel: "strict",
//   validationAction: "error"
// });
// db.admins.insertOne(
//   {
//       user_id: db.users.insertOne({
//         email: "rkc7h@virginia.edu",
//         eppn: "rkc7h@virginia.edu",
//         first_name: "Ravi",
//         last_name: "Chamakuri",
//         phone: "5714391695",
//         display_name: "Ravi Chamakuri",
//         verified: false,
//         alowed_domains: ['virginia.edu'],
//         user_create_date: 'December 07, 2021 22:47 PM'
//       })["insertedId"], 
//       admin_permissions: [
//           { admin_role: "app-admin"},
//           { admin_role: "app-approver"}
//       ]
//   }
// );
// db.users.updateOne(
//     {
//         '_id': db.users.findOne( 
//             {
//                 email: "rkc7h@virginia.edu"
//             }
//         )['_id']
//     },
//     {
//         "$set": {
//             user_update_by_user_id: db.users.findOne( 
//                 {
//                     email: "rkc7h@virginia.edu"
//                 }
//             )['_id'],
//             user_update_date: 'December 07, 2021 22:47 PM'
//         }
//     }
// );
// // db.projects.insertOne({
// //   project_name: "Test Project",
// //   project_desc: "Test Project",
// //   project_create_date: "20160712",
// //   data_sensitivity: "HIPPA",
// //   other_sensitivity_desc: "",
// //   approval_status: "Pending",
// //   approved_by_email: "",
// //   project_approved_date: "",
// //   user_permissions: [
// //     { user_email: "rkc7h@virginia.edu", user_role: "project-admin", is_pi: true},
// //     { user_email: "rkc7h@virginia.edu", user_role: "project-user", is_pi: false}
// //   ]
// // });

