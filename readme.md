# MyCluster project

## System Requirements
MyCluster requires a Linux(ubuntu 18.05 or compatible) environment with docker and docker-compose installation. This project provide Vagrant/Chef scripts to create a virtual machine with those requirements.

Install virtualbox and vagrant in order to create the required enviroment for running the mycluster components

[VirtualBox download](https://www.virtualbox.org/)

[Vagrant download](https://www.vagrantup.com/downloads.html)


### Running the ubuntu-18.05 bionic virtualbox
1. Go to install directory `<your project>/vagrant` directory on your local system
2. run `vagrant up`
    In case you have any issues with the chef-solo recipes, run `vagrant provision`

**Note**: Run `vagrant destroy` in case you want to remove this VM from your system.

The mycluster chef recipe will install  the required softwares (docker and docker-compose) into the VM and create the `/mycluster` diretctory (linked to your `<your project>` directory in the host system ).

### Clone MyCluster project on your environment
Clone this project or download the zip file from github and extract it into your system.

`git clone https://github.com/rbfernan/mycluster.git`

### Setting up you cluster

1. SSH to the VM `vagrant ssh` and switch to root user `sudo su -`  (if running on the virtualbox env)
2. Go to the `cluster` directory  `cd /mycluster/cluster`
3. Setup the new cluster

```
 ./setupCluster.sh -h

Usage: ./setupCluster.sh [options]

Arguments:
  -cn <val>, --clusterName <val>, -cn<val>
    (Optional) Cluster Name. Default is myCluster

  -s, --scaleWorkers
    (Optional) Number of workers to be instantiated in the cluster. Default is 3

```
Run `./setupCluster.sh -cn test -s 4` to create a **test** cluster with 4 worker nodes

Run `docker ps` and you should see the cluster nodes

```
CONTAINER ID        IMAGE               COMMAND                  CREATED              STATUS              PORTS                    NAMES
adbc8c1365b6        docker:dind         "dockerd-entrypoint.…"   32 seconds ago       Up 29 seconds       2375/tcp                 test_worker_4
aab91dad98b6        docker:dind         "dockerd-entrypoint.…"   40 seconds ago       Up 33 seconds       2375/tcp                 test_worker_3
e0fb0f196ac5        docker:dind         "dockerd-entrypoint.…"   40 seconds ago       Up 34 seconds       2375/tcp                 test_worker_2
42a072398fe3        docker:dind         "dockerd-entrypoint.…"   40 seconds ago       Up 35 seconds       2375/tcp                 test_worker_1
094713d49960        test_manager        "python3 app.py"         46 seconds ago       Up 43 seconds       0.0.0.0:5000->5000/tcp   test_manager_1
991f0d85907a        redis:alpine        "docker-entrypoint.s…"   About a minute ago   Up About a minute   6379/tcp                 test_redis_1
```
The cluster is comprised of: 
- A Manager node (test_manager_1), a python web server (based on flask) that exposes the cluster REST APIs
- A Redis node (test_redis_1), to store cluster data
- A Monitor agent for monitoring cluster nodes and rebalance services containers as required in case of any workers failure (to be implemented)
- One or many Workers (test_worker_1 to test_worker_4), based on the docker `docker:dind` [image](https://github.com/jpetazzo/dind) to run the application workloads (docker containers)

### Getting Cluster Stats 

```
curl -H "Content-Type: application/json" -X GET http://localhost:5000/api/v1/stats
```

*Response*

```
{"cluster.upTime": "0:04:42.057918", "services.totalOfRequests": 0, "services.totalOfContainers": 0}
```

### Checking Cluster State

```
curl -H "Content-Type: application/json" -X GET http://localhost:5000/api/v1/state 
```

*Response*

```
{"cluster.name": "test", "cluster.numOfWorkers": 4, "cluster.workers": [{"worker": "test_worker_1", "serviceInstances": []}, {"worker": "test_worker_2", "serviceInstances": []}, {"worker": "test_worker_3", "serviceInstances": []}, {"worker": "test_worker_4", "serviceInstances": []}], "cluster.servicesDef": []}
```

### Creating a new service

```
curl -H "Content-Type: application/json" -X POST -d '{"service": "hello-world" , "image":"crccheck/hello-world", "replicas" : 3 }' http://localhost:5000/api/v1/service
```

*Response*

```
{"cluster.name": "test", "cluster.numOfWorkers": 4, "cluster.workers": [{"worker": "test_worker_1", "serviceInstances": [{"image": "crccheck/hello-world", "numOfRunningContainers": 1}]}, {"worker": "test_worker_2", "serviceInstances": [{"image": "crccheck/hello-world", "numOfRunningContainers": 1}]}, {"worker": "test_worker_3", "serviceInstances": [{"image": "crccheck/hello-world", "numOfRunningContainers": 1}]}, {"worker": "test_worker_4", "serviceInstances": []}], "cluster.servicesDef": [{"service": "hello-world1", "image": "crccheck/hello-world", "replicas": 3, "last_updated": 1559685228}]}
```

*Check the registered service*

```
curl -H "Content-Type: application/json" -X GET http://localhost:5000/api/v1/service/hello-world
```

*Response*

```
{"service": "hello-world", "image": "crccheck/hello-world", "replicas": 3, "last_updated": 1559662887}
```

### Checking *worker* nodes directly via *manager* container

```
docker exec -it test_manager_1 docker -H test_worker_1 ps
docker exec -it test_manager_1 docker -H test_worker_2 ps
docker exec -it test_manager_1 docker -H test_worker_3 ps
docker exec -it test_manager_1 docker -H test_worker_4 ps
```

### Managing the Cluster

Go to the `/mycluster/cluster` directory

```
cd /mycluster/cluster

./manageCluster.sh -h
Usage: ./manageCluster.sh [options]

Arguments:
  -c up | stop | rm | ps , --command up | stop | rm | ps
  (Required) Command to be run against the cluster.
```

Stopping all cluster containers

`./manageCluster.sh -c stop`

Removing all cluster containers

`./manageCluster.sh -c rm`
