import os

from tools.general import DBhandler, create_payments, interface, compute_delay_v2, compute_delay_v3


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
create_payments(db_connection, os.path.join(DATA_DIR, "payments.xls"))
db_connection.join_tables(table1="profile_contract", table2="payment", left_key="contract_id", right_key="contract_id")

compute_delay_v3(db_connection)
interface(db_connection)
