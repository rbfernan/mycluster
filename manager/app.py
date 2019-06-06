#!/usr/local/bin/python3
# see issue https://github.com/pallets/werkzeug/issues/1482 for the line above

# Dependencies:
# pip install flask
# pip install redis

import flask , time, json, logging,  datetime
import config, manager
from flask import Flask
from flask import request
from flask import Response, stream_with_context
from logging.handlers import RotatingFileHandler
from flask_expects_json import expects_json

app = Flask(__name__)
app.debug = True

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
    manager.deleteDbService(serviceKey)

    eventStr = json.dumps(event)
    manager.setDbService(serviceKey, eventStr)

    # TODO Add error handling here
    manager.deployContainerToCluster(event['image'] , event['replicas'])

    stats = manager.getClusterState()
    return json.dumps(stats), 201


@app.route(config.DEFAULT_API_PATH + "/service/<service>", methods = ['GET'])
def service(service):
    event = request.json
    serviceKey= config.NS_SERVICES + service
    if not manager.existsDbService(serviceKey):
        # TODO fix proper response
        return json.dumps({"message" : "Service "+ str(service) +" was not registred for this cluster.", "code" : 404 }), 404

    event = manager.getDbService(serviceKey)
    result = json.loads(event)
    print(f'this is the service event --> {event}')
    return json.dumps(result), 200

@app.route(config.DEFAULT_API_PATH + "/state", methods = ['GET'])
def state():
    event = manager.getClusterState()    
    return json.dumps(event), 200

@app.route(config.DEFAULT_API_PATH + "/stats", methods = ['GET'])
def stats():
    event = manager.getClusterStats()    
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
