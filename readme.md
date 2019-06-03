# MyCluster project

## System Requirements
Install virtualbox and vagrant in order to create the required enviroment for running the mycluster components

[VirtualBox download](https://www.virtualbox.org/)

[Vagrant download](https://www.vagrantup.com/downloads.html)

Then clone this project or download the zip file from github and extract it into your system.

### Running the ubuntu-18.05 bionic virtualbox
1. Go to install directory `<your project>/vagrant` directory on your local system
2. run `vagrant up`
    In case you have any issues with the chef-solo recipes, run `vagrant provision`
Run `vagrant destroy` in case you want to remove this VM from your system.

The mycluster chef recipe will install  the required softwares (docker and docker-compose) into the VM and create the `/mycluster` diretctory (linked to your `<your project>` directory in the host system ).

### Setting up you cluster

1. SSH to the VM `vagrant ssh`
2. Switch to root user `sudo su -`
3. Go to the `cluster` directory  `cd /mycluster/cluster`
4. Setup the new cluster

```
 ./setupCluster.sh -h

Usage: ./setupCluster.sh [options]

Arguments:
  -cn <val>, --clusterName <val>, -cn<val>
    (Optional) Cluster Name. Default is myCluster

  -s, --scaleWorkers
    (Optional) Number of workers to be instantiated in the cluster. Default is 3

```
Run `./setupCluster.sh -cn test -s 4` to create a `test` cluster with 4 worker nodes

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
1. A manager node (test_manager_1), a python web server (based on flask) that exposes the cluster REST APIs
2. A Redis db (test_redis_1), to store cluster data
3. One or many Workers (test_worker_1 to test_worker_4), based on the docker `docker:dind` image (https://github.com/jpetazzo/dind) to run the application workloads (docker containers)

### Getting Cluster Stats 
```
curl -H "Content-Type: application/json" -X GET http://localhost:5000/api/v1/stats
{"cluster.upTime": "0:04:42.057918", "services.totalOfRequests": 0, "services.totalOfContainers": 0}
```

### Checking Cluster State
```
curl -H "Content-Type: application/json" -X GET http://localhost:5000/api/v1/state 
{"cluster.name": "test", "cluster.numOfWorkers": 4, "cluster.workers": ["test_worker_1", "test_worker_2", "test_worker_3", "test_worker_4"], "cluster.servicesDef": []}
```

### Creating a new service
```
curl -H "Content-Type: application/json" -X POST -d '{"service": "hello-world" , "image":"crccheck/hello-world", "replicas" : 3 }' http://localhost:5000/api/v1/service
```

### Checking `worker` nodes directly via `manager` container

```
docker exec -it test_manager_1 docker -H test_worker_1 ps
docker exec -it test_manager_1 docker -H test_worker_2 ps
docker exec -it test_manager_1 docker -H test_worker_3 ps
docker exec -it test_manager_1 docker -H test_worker_4 ps
```

### Managing the Cluster

Go to the `cluster` directory

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
