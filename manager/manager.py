import os, config, docker ,logging, redis, datetime, json, requests
import config, sys

logger = logging.getLogger(__name__)

#connect to server
db = redis.Redis(host=config.getClusterName()+"_redis_1", port=config.DEFAULT_REDIS_PORT) 
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
        "cluster.name" :  config.getClusterName(),
        "cluster.numOfWorkers" : config.getNumOfClusterWorkers(),
        "cluster.workers" : getyWorkersState(),
        "cluster.servicesDef" : listOfServices
    }
    return event

def getyWorkersState():
    listOfWorkers=[]
    workerIds=getWorkerIds()
    for workerId in workerIds:
        workerDict = {
            "worker" : workerId,
            "serviceInstances" :  getInstancesbyWorkerFromDocker(workerId)
        } 
        listOfWorkers.append(workerDict)
    return listOfWorkers

#
# Return an array of images and instances according to what is running on docker
#
def getInstancesbyWorkerFromDocker(workerId, allContainers=False):
    keys = db.keys( "worker." + workerId + ".containers." + "*")
    listOfImagesInstances=[]
    for key in keys:
        sKey=str(key,config.DEFAULT_ENCODING)
        image=sKey.split(".")[-1]
        try:
            client = docker.DockerClient(base_url='tcp://' + workerId +':'+ str(config.DEFAULT_DOCKER_PORT))
            containers = client.containers.list(allContainers, filters={"ancestor":image})
            listOfImagesInstances.append( {"image" : image, "numOfRunningContainers" :len(containers) })
        except requests.exceptions.ConnectionError:
            logger.error(f"Worker {workerId} seems to be down.. can't get state.")
    return listOfImagesInstances

#
# Return an array of images and instances according to the info registered in the database
#
def getInstancesbyWorkerFromDb(workerId):
    keys = db.keys( "worker." + workerId + ".containers." + "*")
    listOfImagesInstances=[]
    for key in keys:
       sKey=str(key,config.DEFAULT_ENCODING)
       image=sKey.split(".")[-1]
       listOfImagesInstances.append( {"image" : image, "numOfContainers" : int(db.get(str(key,config.DEFAULT_ENCODING)))})
    return listOfImagesInstances

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

#
# get worker ids from system configuration
#
def getWorkerIds(all=True):
    # Get this values from Env Vars
    COMPOSE_PROJECT_NAME = config.getClusterName()
    SCALE_WORKERS = config.getNumOfClusterWorkers()

    workerIds = [COMPOSE_PROJECT_NAME+"_worker_" + str(x+1) for x in range(SCALE_WORKERS)]
    logger.debug(f"List of workerIds {workerIds}")
    if not all:
        # Get only running workers
        runningWorkerIds=[]
        logger.debug("Going only for running workers")
        for workerId in workerIds:
            try:
                client = docker.DockerClient(base_url='tcp://' + workerId +':'+ str(config.DEFAULT_DOCKER_PORT))
                client.containers.list()
                runningWorkerIds.append(workerId)  # It is a running one
            except requests.exceptions.ConnectionError:
                logger.error(f"Worker {workerId} seems to be down.. skipping to next in the queue.")
        return runningWorkerIds
    return workerIds
#
# Order the Dictonary { wokerId: TotalOfRunningContainers} by TotalOfRunningContainers ascending
#
def getNextWorkerToDeploy(dictOfTotContainersByWorkers):
    # Create a list of tuples sorted by index 1 i.e. value field        
    orderedNodes = sorted(dictOfTotContainersByWorkers.items() ,  key=lambda x: x[1]) 
    # Get the first element
    for elem in orderedNodes :
        try:
            workerId = elem[0]
            client = docker.DockerClient(base_url='tcp://' + workerId +':'+ str(config.DEFAULT_DOCKER_PORT))
            client.containers.list()       
            return(workerId)
        except requests.exceptions.ConnectionError:
            logger.error(f"Worker {workerId} seems to be down.. skipping to next in the queue.")
            # get next 
                 
#
# Increment the total of running containers for a specific Worker Id
#
def incrementNodeCount(dictOfTotContainersByWorkers, workerId):
    for key,value in dictOfTotContainersByWorkers.items():
        if key == workerId:
            dictOfTotContainersByWorkers[key] = value + 1
            break

#
# Build a dictionary with the following structure 
# 
#  { wokerId: TotalOfRunningContainers}
#              
#  example: {'mycluster_worker_0': 7, 'mycluster_worker_1': 6, 'mycluster_worker_2': 8}
#
def buildDictWithTotalContainersbyWokers():
    workerIds=getWorkerIds(False)
    return dict((workerId, getTotalOfContainersForWorker(workerId)) for workerId in workerIds)

#  
# Get containers info from docker for a given worker
#     
def getTotalOfContainersForWorker(workerId):
    try:
        client = docker.DockerClient(base_url='tcp://' + workerId +':'+ str(config.DEFAULT_DOCKER_PORT))
        containers = client.containers.list()
        print (f' Total of {len(containers)} containers started on {workerId}')
        print(containers)
        return len(containers)
        #return randint(0, 3)

    except docker.errors.DockerException as error:
        logger.error(error)
        raise

def deployContainerToWorker(workerId, image):
    # Run a container      
    try:
        #client = docker.DockerClient(base_url='tcp://localhost:2375')
        client = docker.DockerClient(base_url='tcp://' + workerId +':'+ str(config.DEFAULT_DOCKER_PORT))
        container = client.containers.run(image, detach=True)
        print (f'docker container {container.name} started on {workerId}')
    # except requests.exceptions.ConnectionError as e:
    #     logger.error(f"Worker {workerId} was not found... realocating its services")
    #     raise e
    except Exception as error:
        logger.error(error)
        raise error

def deployContainerToCluster(image, replicas):
    workers = buildDictWithTotalContainersbyWokers() 
    logger.debug(f"deployContainerToCluster, workers= {workers}" )

   # collect some Stats here    
    db.incr(config.STATS_SEVICE_REQUESTS)
    success = False
    #db.incr(config.STATS_SEVICE_CONTAINERS, replicas)
    for i in range(replicas): 
        nextWorkerToDeploy = getNextWorkerToDeploy(workers)
        if nextWorkerToDeploy != None:
            success = True   #at least one worker was available
            logger.info(f"New {image} container will be deployed to {nextWorkerToDeploy}")
            try:
                deployContainerToWorker(nextWorkerToDeploy,image)
                # increment containers for worker/image
                workerContainers = getWorkerContainersDbKey(nextWorkerToDeploy,image)
                db.incr(workerContainers)
                db.incr(config.STATS_SEVICE_CONTAINERS)
            except Exception as error:
                logger.error(error)
                raise
            else:
                incrementNodeCount(workers, nextWorkerToDeploy )  

    if (not success):
        logger.error(f"All workers seem to be down")

    return success
#
# Realocate service instances from a given worker to other available workers
# 
def realocateServices(workerId):
     logger.info(f"Realocating services from worker {workerId}")
     lstImages = getInstancesbyWorkerFromDb(workerId)
     logger.debug(f"lstImages = {lstImages}" )
     for imageDict in lstImages:
        image = imageDict["image"]
        numOfContainers = imageDict["numOfContainers"]
        if numOfContainers > 0: 
            logger.debug(f"realocating image {image} , {numOfContainers} containers")
            if deployContainerToCluster(image, numOfContainers):
                decrDbWorkerImage(workerId, image,numOfContainers)
        else:
            logger.info(f"No services assigned for worker {workerId}")  

# DBKey to store num of containers images per worker
def getWorkerContainersDbKey(nextWorkerToDeploy,image):
    return "worker." + nextWorkerToDeploy + ".containers." + image

#deployContainerToCluster("crccheck/hello-world" , 5)
def getDbService(serviceKey):
    return db.get(serviceKey) 

def setDbService(serviceKey, eventStr):
    db.set(serviceKey, eventStr)

def deleteDbService(serviceKey):
    db.delete(serviceKey) 

def existsDbService(serviceKey):
    return db.exists(serviceKey)

def decrDbWorkerImage(workerId, image, amount=1):
    name = getWorkerContainersDbKey(workerId,image)
    db.decr(name, amount)

if __name__ == "__main__":
    # TO be run on a short interval
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)