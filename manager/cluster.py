import os, config, docker ,logging
from random import randint

logger = logging.getLogger(__name__)

def getClusterName():
    return os.getenv('COMPOSE_PROJECT_NAME', config.DEFAULT_COMPOSE_PROJECT_NAME)

def getNumOfClusterWorkers():
    return int(os.getenv("SCALE_WORKERS",config.DEFAULT_SCALE_WORKERS))

#
# get worker ids from system configuration
#
def getWorkerIds():
    # Get this values from Env Vars
    COMPOSE_PROJECT_NAME = getClusterName()
    SCALE_WORKERS = getNumOfClusterWorkers()

    workerIds = [COMPOSE_PROJECT_NAME+"_worker_" + str(x+1) for x in range(SCALE_WORKERS)]
    print(workerIds)
    return workerIds
#
# Order the Dictonary { wokerId: TotalOfRunningContainers} by TotalOfRunningContainers ascending
#
def orderWorkersByContainersCount(dictOfTotContainersByWorkers):
    # Create a list of tuples sorted by index 1 i.e. value field        
    orderedNodes = sorted(dictOfTotContainersByWorkers.items() ,  key=lambda x: x[1]) 
    # Get the first element
    for elem in orderedNodes :
        return(elem[0])
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
    workerIds=getWorkerIds()
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

    except docker.errors.DockerException as error:
        logger.error(error)
        raise

def deployContainerToCluster(image, replicas):
    workers = buildDictWithTotalContainersbyWokers() 
    print(workers)
 
    for i in range(replicas): 

        nextWorkerToDeploy = orderWorkersByContainersCount(workers)
        print (f"New {image} container will be deployed to {nextWorkerToDeploy}")

        try:
            deployContainerToWorker(nextWorkerToDeploy,image)
        except Exception as error:
            logger.error(error)
            raise
        else:
            incrementNodeCount(workers, nextWorkerToDeploy )  

#deployContainerToCluster("crccheck/hello-world" , 5)

