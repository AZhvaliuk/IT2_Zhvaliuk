import os

from tools.general import DBhandler, select_peoples


ROOT_DIR = os.getcwd()
DATA_DIR = os.path.join(ROOT_DIR, "data")
DATABASE_DIR = os.path.join(ROOT_DIR, "database")
DATABASE_NAME = "origin.db"
DATABASE_PATH = os.path.join(DATABASE_DIR, DATABASE_NAME)
STATIC_PATH = os.path.join(ROOT_DIR, "images")

if not os.path.exists(DATA_DIR):
    raise Exception("DATA_DIR is missing")
if not os.path.exists(DATABASE_DIR):
    os.makedirs(DATABASE_DIR)
if not os.path.exists(STATIC_PATH):
    os.makedirs(STATIC_PATH)

db_connection = DBhandler(type_="pyodbc", db_path=DATABASE_PATH)
select_peoples(db_connection)
