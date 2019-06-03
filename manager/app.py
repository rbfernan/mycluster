#!/usr/local/bin/python3
# see issue https://github.com/pallets/werkzeug/issues/1482 for the line above

# Dependencies:
# pip install flask
# pip install redis

import flask ,redis , time, json, logging,  datetime
import config, cluster
from flask import Flask
from flask import request
from flask import Response, stream_with_context
from logging.handlers import RotatingFileHandler
from flask_expects_json import expects_json

app = Flask(__name__)
app.debug = False
#connect to server
db = redis.Redis(host=cluster.getClusterName()+"_redis_1", port=config.DEFAULT_REDIS_PORT) 
managerStartUpTime = datetime.datetime.now() 

def getClusterStats():
    statsRequests = 0
    statsContainers = 0
    if db.exists(config.STATS_SEVICE_REQUESTS):
        statsRequests= int(db.get(config.STATS_SEVICE_REQUESTS))    
    if db.exists(config.STATS_SEVICE_CONTAINERS):
        statsContainers= int(db.get(config.STATS_SEVICE_CONTAINERS))

    event = {   
        "cluster.upTime" : str((datetime.datetime.now()- managerStartUpTime)),
        "services.totalOfRequests" : statsRequests,   
        "services.totalOfContainers" : statsContainers               
    }
    return event

def getClusterState():  

    listOfServices=[]
    keys = db.keys(config.NS_SERVICES + "*")
    for key in keys:
       listOfServices.append(json.loads(db.get(str(key,config.DEFAULT_ENCODING))))

    event = {   
        "cluster.name" :  cluster.getClusterName(),
        "cluster.numOfWorkers" : cluster.getNumOfClusterWorkers(),
        "cluster.workers" : cluster.getWorkerIds(),        
        "cluster.servicesDef" : listOfServices
    }
    return event
   

# def get_hit_count():
#     retries = 5
#     while True:
#         try:
#             return db.incr('stats.services.requests')
#         except redis.exceptions.ConnectionError as exc:
#             if retries == 0:
#                 raise exc
#             retries -= 1
#             time.sleep(0.5)

# Default unexpect exception
@app.errorhandler(Exception)
def handle_error(e):
    # TODO Improve error handing
    app.logger.error(str(e))
    return  json.dumps({"error": str(e), "code" : 500 }), 500  

serviceReqSchema = {
    'type': 'object',
    'properties': {
        'service': {'type': 'string'},
        'image': {'type': 'string'},
        'replicas': {'type': 'integer'}
    },
    'required': ['service', 'image', 'replicas']
}
@app.route(config.DEFAULT_API_PATH + "/service", methods = ['POST'])
@expects_json(serviceReqSchema)
def serviceCreate():
    event = request.json       
    serviceKey= config.NS_SERVICES + event['service']
    event['last_updated'] = int(time.time())
    #remove old keys for simplicity for now TODO Review duplications
    db.delete(serviceKey) 

    eventStr = json.dumps(event)
    db.set(serviceKey, eventStr)

    # TODO Add error handling here
    cluster.deployContainerToCluster(event['image'] , event['replicas'])

    # collect some Stats here    
    db.incr(config.STATS_SEVICE_REQUESTS)
    db.incr(config.STATS_SEVICE_CONTAINERS, event['replicas'])

    stats=getClusterState()
    return json.dumps(stats), 201


@app.route(config.DEFAULT_API_PATH + "/service/<service>", methods = ['GET'])
def service(service):
    event = request.json
    serviceKey= config.NS_SERVICES + service
    if not db.exists(serviceKey):
        # TODO fix proper response
        return "Error: Service"+ str(service) +" was not registred for this cluster."   

    event = db.get(serviceKey)
    result = json.loads(event)
    print(f'this is the service event --> {event}')
    return json.dumps(result), 200

@app.route(config.DEFAULT_API_PATH + "/state", methods = ['GET'])
def state():
    event = getClusterState()    
    return json.dumps(event), 200

@app.route(config.DEFAULT_API_PATH + "/stats", methods = ['GET'])
def stats():
    event = getClusterStats()    
    return json.dumps(event), 200

@app.route("/testlog")
def logTest():
    app.logger.info('testing info log')
    app.logger.warning('testing warning log')
    app.logger.error('testing error log')
    return "Log testing OK"

if __name__ == "__main__":
    # initialize the log handler  
    logging.getLogger().setLevel(logging.INFO)
    formatter = logging.Formatter(
        "[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s")
    logHandler = RotatingFileHandler('manager.log', maxBytes=1000, backupCount=1)
    logHandler.setFormatter(formatter)
    logHandler.setLevel(logging.INFO)
    app.logger.addHandler(logHandler)
    app.run(host='0.0.0.0', port=config.DEFAULT_API_PORT)
