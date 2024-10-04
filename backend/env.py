import os

VERSION = "{{VERSION_PLACEHOLDER}}" if not "{" in "{{VERSION_PLACEHOLDER}}" else "0.0.0"
DEBUG = os.getenv("DEBUG", "").lower() in ["true", "1", "t"]
CORS_ALLOW = os.getenv("CORS_ALLOW", "").lower() in ["true", "1", "t"]
RESET_DB_DANGEROUS = os.getenv("RESET_DB_DANGEROUS", "").lower() in ["true", "1", "t"]

JWT_ALGORITHM = "HS256"
#JWT_EXPIRE_H = 3

POSTGRES_USER = os.getenv("POSTGRES_USER", "exploitfarm")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "exploitfarm")
POSTGRES_DB = os.getenv("POSTGRES_DB", "exploitfarm")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1" if DEBUG else "database")
DB_PORT = os.getenv("DB_PORT", "5432")
NTHREADS = int(os.getenv("NTHREADS", "3"))
POSTGRES_URL = os.getenv("POSTGRES_URL", f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{DB_HOST}:{DB_PORT}/{POSTGRES_DB}")

EXPLOIT_SOURCES_DIR = "./db-data/exploit-sources"

FLAG_UPDATE_POLLING = 5