import sys, os
import logging
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0,"/home/aboro/projects/register-runner")

os.putenv('FLASK_CONFIG', 'production')

from app import create_app
config_name = os.getenv('FLASK_CONFIG')
config_name = 'production'
application = create_app(config_name)
