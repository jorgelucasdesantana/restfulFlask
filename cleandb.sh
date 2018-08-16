#!/usr/bin/env mongo
var db = new Mongo().getDB("VideoControl");
db.dropDatabase();
