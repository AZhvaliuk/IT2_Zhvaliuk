import os

from tools.general import DBhandler, create_profile, create_contract
from tools.tests import test1


ROOT_DIR = os.getcwd()
DATA_DIR = os.path.join(ROOT_DIR, "data")
DATABASE_DIR = os.path.join(ROOT_DIR, "database")
DATABASE_NAME = "origin.db"
DATABASE_PATH = os.path.join(DATABASE_DIR, DATABASE_NAME)

if not os.path.exists(DATA_DIR):
    raise Exception("DATA_DIR is missing")
if not os.path.exists(DATABASE_DIR):
    os.makedirs(DATABASE_DIR)

db_connection = DBhandler(db_path=DATABASE_PATH)
create_profile(connection=db_connection, data_path=DATA_DIR)
create_contract(connection=db_connection, data_path=DATA_DIR)

# TESTS
test1(db_connection)


# CREATING MAP
db_connection.create_map(values_map={"Female": 0, "Male": 1}, target_table="profile", target_column="gender")
db_connection.create_map(values_map={"Secondary / secondary special": 1,
                                     "Incomplete higher": 2,
                                     "Higher education": 3}, target_table="profile", target_column="education")
db_connection.create_map(values_map={"Separated": 0,
                                     "Single / not married": 0,
                                     "Widow": 0,
                                     "Married": 1,
                                     "Civil marriage": 1}, target_table="profile", target_column="marital_status")
db_connection.create_map(values_map={"House / apartment": 1,
                                     "Municipal apartment": 0,
                                     "Rented apartment": 0,
                                     "With parents": 0}, target_table="profile", target_column="housing")
db_connection.create_map(values_map={"Cash loans": 1,
                                     "Revolving loans": 0}, target_table="contract", target_column="type")

# JOIN TABLES
db_connection.join_tables(table1="profile", table2="contract", left_key="id", right_key="id")
