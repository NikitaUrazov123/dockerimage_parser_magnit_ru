# config/settings.py

import os
from . import db_config

ENV = os.getenv("APP_ENV", "dev")

if ENV == "prod":
    DB_SETTINGS = db_config.PROD_DB
else:
    DB_SETTINGS = db_config.DEV_DB
