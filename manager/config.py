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
STATS_SEVICE_REQUESTS = "stats.services.requests"
STATS_SEVICE_CONTAINERS = "stats.services.containers"
