# MyCluster project

## System Requirements
MyCluster only requires a Linux(ubuntu 18.05 or compatible) with docker and docker-compose installed. The project also provides Vagrant/Chef scripts to create the Linux virtual machine with the base requirements. Follow the links bellow to install Virtualbox and Vagrant in order to run them:

[VirtualBox download](https://www.virtualbox.org/)

[Vagrant download](https://www.vagrantup.com/downloads.html)

After the installation, please follow the steps below:

### Clone the MyCluster project on your environment
Clone this project or download the zip file from github and extract it into your system.

`git clone https://github.com/rbfernan/mycluster.git`

### Running the ubuntu-18.05 bionic virtualbox
1. Go to install directory `<your project>/vagrant` directory on your local system
2. run `vagrant up`   (This process can't take several minutes)

    In case you have any issues with the chef-solo recipes, run `vagrant provision`

**Note**: Run `vagrant destroy` in case you want to remove this VM from your system later on.

The mycluster chef recipe will install  the required softwares (docker and docker-compose) into the VM and create the `/mycluster` diretctory (linking it to `<your project>` directory in the host system ).


### Setting up you cluster

1. SSH to the VM `vagrant ssh` and switch to root user `sudo su -`  (if running on the virtualbox env)
2. Go to the `cluster` directory  `cd /mycluster/cluster`
3. Setup a new cluster

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
CONTAINER ID        IMAGE               COMMAND                  CREATED             STATUS              PORTS                    NAMES
877bc28ffd21        docker:dind         "dockerd-entrypoint.…"   11 minutes ago      Up 11 minutes       2375/tcp                 test_worker_3
792a43f240cb        docker:dind         "dockerd-entrypoint.…"   11 minutes ago      Up 11 minutes       2375/tcp                 test_worker_1
bd5fe14a589d        docker:dind         "dockerd-entrypoint.…"   11 minutes ago      Up 11 minutes       2375/tcp                 test_worker_4
8cb064bccb53        docker:dind         "dockerd-entrypoint.…"   11 minutes ago      Up 11 minutes       2375/tcp                 test_worker_2
eff48b63dbc5        test_monitor        "python3 monitor.py"     11 minutes ago      Up 11 minutes                                test_monitor_1
73d9c39bd16d        test_manager        "python3 app.py"         11 minutes ago      Up 11 minutes       0.0.0.0:5000->5000/tcp   test_manager_1
67ff146f6066        redis:alpine        "docker-entrypoint.s…"   11 minutes ago      Up 11 minutes       6379/tcp                 test_redis_1
```
The cluster is comprised of: 
- A Manager node *(test_manager_1)*, a python web server (based on flask) that exposes the cluster REST APIs
- A Redis node *(test_redis_1)*, to store cluster data
- A Monitor agent node *(test_monitor_1)* for monitoring cluster worker nodes and relocate services containers as required in case of any failures (running by default on a 30 sec interval)
- One or many Workers *(test_worker_1 to test_worker_4)*, based on the docker [`docker:dind`](https://github.com/jpetazzo/dind) image to run application workloads (docker containers)

### Getting Cluster Stats 

```
curl -H "Content-Type: application/json" -X GET http://localhost:5000/api/v1/stats
```

*Response*

```
{"cluster.upTime": "0:03:45.060206", "services.totalOfRequests": 0, "services.totalOfContainers": 0, "workers.failures": 0, "containers.relocated": 0}
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

### Checking the Monitor agent logs

For checking the log

``` 
docker logs -f test_monitor_1
```

### Simulating a Failure

To simulate a failure in one of the workers node and see the automatic relocation of its containers to the remaining available nodes.

``` 
docker stop test_worker_1
```

See the detailed info in the monitor log output
```
[2019-06-06 11:28:28,383] {monitor.py:12} INFO - Starting monitor agent
[2019-06-06 11:28:28,579] {monitor.py:23} ERROR - Worker test_worker_1 was not found... realocating its services
[2019-06-06 11:28:28,587] {/code/manager.py:214} INFO - Realocating services from worker test_worker_1
[2019-06-06 11:28:28,727] {/code/manager.py:114} ERROR - Worker test_worker_1 seems to be down.. skipping to next in the queue.
[2019-06-06 11:28:28,865] {/code/manager.py:161} INFO -  Total of 1 containers started on test_worker_2
[2019-06-06 11:28:28,868] {/code/manager.py:162} INFO - [<Container: 7b6268a006>]
[2019-06-06 11:28:28,911] {/code/manager.py:161} INFO -  Total of 1 containers started on test_worker_3
[2019-06-06 11:28:28,912] {/code/manager.py:162} INFO - [<Container: 8c452d4920>]
[2019-06-06 11:28:28,943] {/code/manager.py:161} INFO -  Total of 0 containers started on test_worker_4
[2019-06-06 11:28:28,944] {/code/manager.py:162} INFO - []
[2019-06-06 11:28:28,969] {/code/manager.py:193} INFO - New crccheck/hello-world container will be deployed to test_worker_4
[2019-06-06 11:28:36,155] {/code/manager.py:176} INFO - docker container wizardly_villani started on test_worker_4
[2019-06-06 11:28:36,237] {/code/manager.py:161} INFO -  Total of 1 containers started on test_worker_2
[2019-06-06 11:28:36,239] {/code/manager.py:162} INFO - [<Container: 7b6268a006>]
[2019-06-06 11:28:36,299] {/code/manager.py:161} INFO -  Total of 1 containers started on test_worker_3
[2019-06-06 11:28:36,299] {/code/manager.py:162} INFO - [<Container: 8c452d4920>]
[2019-06-06 11:28:36,347] {/code/manager.py:161} INFO -  Total of 1 containers started on test_worker_4
[2019-06-06 11:28:36,347] {/code/manager.py:162} INFO - [<Container: 353845a235>]
[2019-06-06 11:28:36,360] {monitor.py:14} INFO - Stopping monitor agent
````
