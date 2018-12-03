import json, os
from pymongo import MongoClient

def handler(event, context):

    inserts = []

    if 'Records' in event:
        # open mongodb connection
        client = MongoClient(os.environ['mongo_connection'])
        db = client[os.environ['mongo_database']]
        coll = db[os.environ['mongo_collection']]

        for record in event['Records']:
            insert_id = coll.insert_one(json.loads(record['body'])).inserted_id
            inserts.append(insert_id)

    return {'inserts': inserts}

