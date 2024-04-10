import pymongo

def id_request(service_name):
    db_client = pymongo.MongoClient('mongodb://localhost:27017/')
    db = db_client['vpniddb']
    collection = db['vpnid']
    x = collection.find_one({'seized': False})
    vpn_id = x['id']
    collection.update_one({'id': vpn_id}, {'$set':{'seized': True, 'user': 'l3vpnmongo-'+service_name}})
    return vpn_id

def id_read(vpn_id):
    print(vpn_id)
