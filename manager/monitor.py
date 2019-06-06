'''
Monitors workers nodes and containers
'''
import os, config, docker ,logging
import config, manager
import logging, requests
import sys
import threading

def run():
    threading.Timer(config.MONITOR_EXEC_INTERVAL, run).start()
    logger.info("Starting monitor agent")
    monitorWorkers()
    logger.info("Stopping monitor agent")

def monitorWorkers():
    workerIds=manager.getWorkerIds()
    for workerId in workerIds:
        try:
            manager.getTotalOfContainersForWorker(workerId)

        except requests.exceptions.ConnectionError:
            logger.error(f"Worker {workerId} was not found... realocating its services")
            manager.realocateServices(workerId)
        except Exception as e:
            logger.error(f" unexpected error {type(e)},{str(e)}")

if __name__ == "__main__":
    # TO be run on a short interval
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter("[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    run()
    
