import os
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg:///shortlink_app_dev")

