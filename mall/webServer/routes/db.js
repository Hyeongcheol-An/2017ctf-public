// node-mysql
var config = require('./config.js');
var mysql = require('mysql');

var rs = require('readline-sync');
config.database.password = rs.question('DB Password: ');
config.PASSWORD = rs.question('GPG PASSPHRASE: ');

// DataBase Config
var client = mysql.createConnection( config.database );

// running queries as normal...
client.query('USE shoppingmalldb');

// mysql-queues
var queues = require('mysql-queues');
const DEBUG = true;
queues(client, DEBUG);
var q = client.createQueue();

module.exports = q;
