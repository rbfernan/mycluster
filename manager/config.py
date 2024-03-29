import os

# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))

# Enable debug mode.
DEBUG = True

# Default values
DEFAULT_DOCKER_PORT=2375
DEFAULT_REDIS_HOST="localhost"
DEFAULT_REDIS_PORT=6379
DEFAULT_ENCODING='utf-8'

DEFAULT_API_PATH="/api/v1"
DEFAULT_API_PORT=5000

# Env Variables defaults
DEFAULT_COMPOSE_PROJECT_NAME = "mycluster"
DEFAULT_SCALE_WORKERS = 0

# DATA namespaces
NS_SERVICES = "services."

# Stats
STATS_SERVICE_REQUESTS = "stats.services.requests"
STATS_SERVICE_CONTAINERS = "stats.services.containers"
STATS_WORKERS_FAILURES = "stats.workers.failures"
STATS_CONTAINERS_RELOCATIONS = "stats.containers.relocations"

# Monitor
MONITOR_EXEC_INTERVAL=30.0

def getClusterName():
    return os.getenv('COMPOSE_PROJECT_NAME', DEFAULT_COMPOSE_PROJECT_NAME)

def getNumOfClusterWorkers():
    return int(os.getenv("SCALE_WORKERS",DEFAULT_SCALE_WORKERS))
