import xlrd
from datetime import datetime, timedelta
import os
import pandas as pd
from tabulate import tabulate
import math
import numpy as np
from sklearn.metrics import roc_curve
import matplotlib.pyplot as plt
from dateutil.relativedelta import relativedelta


class DBhandler:
    def __init__(self, db_path=None, type_="sqlite3"):
        """
        """
        if not db_path:
            raise Exception("db_path is required")

        if type_ == "pyodbc":
            import pyodbc
            conection_config = "DRIVER={SQLite3 ODBC Driver};SERVER=localhost;DATABASE=%s;Trusted_connection=yes" % db_path
            self.connection = pyodbc.connect(conection_config)
            self.cursor = self.connection.cursor()
        elif type_ == "sqlite3":
            import sqlite3
            self.connection = sqlite3.connect(db_path)
            self.cursor = self.connection.cursor()
        else:
            raise Exception("Incorrect type")

    def execute_sql(self, raw_sql, commit=False):
        self.cursor.execute(raw_sql)
        if commit:
            self.connection.commit()

    def create_table(self, type_=None):
        if not type_:
            raise Exception("type_ is required")
        if type_ == "profile":
            sql_query = """CREATE TABLE IF NOT EXISTS profile
            (
                id INTEGER NOT NULL,
                birth TEXT,
                gender TEXT,
                employed_by TEXT,
                issue_date TEXT,
                education TEXT,
                children INTEGER,
                family INTEGER,
                marital_status TEXT,
                position TEXT,
                housing TEXT,
                income INTEGER
            )"""
        elif type_ == "contract":
            sql_query = """CREATE TABLE IF NOT EXISTS contract
            (
                id INTEGER NOT NULL,
                contract_id INTEGER,
                amount INTEGER,
                type TEXT,
                month_term INTEGER,
                annuity INTEGER
            )"""
        elif type_ == "payment":
            sql_query = """CREATE TABLE IF NOT EXISTS payment
            (
                contract_id INTEGER NOT NULL,
                payment_date TEXT,
                amount_due REAL,
                amount_paid REAL
            )
            """
        elif type_ == "payment_delay":
            sql_query = """CREATE TABLE IF NOT EXISTS payment_delay
            (
                contract_id INTEGER NOT NULL,
                payment_date TEXT,
                payment_delay INTEGER,
                status TEXT
            )"""
        elif type_ == "payment_delay_max":
            sql_query = """CREATE TABLE IF NOT EXISTS payment_delay_max
            (
              contract_id INTEGER NOT NULL,
              payment_delay INTEGER
            )"""
        elif type_ == "temp":
            sql_query = """CREATE TABLE IF NOT EXISTS temp
            (
                payment_day1 TEXT,
                payment_delay INTEGER,
                status TEXT,
                contract_id INTEGER NOT NULL
            )"""
        else:
            sql_query = ""

        self.execute_sql(raw_sql=sql_query, commit=True)

    def join_tables(self, table1, table2, left_key, right_key):
        sql_template = """CREATE TABLE IF NOT EXISTS {}_{} AS
            SELECT * FROM {} as table1
            JOIN {} as table2
                ON table1.{} = table2.{}
        """.format(table1, table2, table1, table2, left_key, right_key)
        self.cursor.execute(sql_template)
        self.connection.commit()

    def create_map(self, values_map, target_table, target_column):
        create_sql = """CREATE TABLE IF NOT EXISTS values_map (key TEXT, value TEXT, table_name TEXT)"""
        self.cursor.execute(create_sql)
        self.connection.commit()

        insert_temp = """INSERT INTO values_map VALUES (?, ?, ?)"""
        update_temp = """UPDATE {} SET {} = '{}' WHERE {} = '{}'"""
        for pair in values_map.items():
            self.cursor.execute(insert_temp, [pair[0], pair[1], target_table])
            self.cursor.execute(update_temp.format(target_table, target_column, pair[1], target_column, pair[0]))
        self.connection.commit()


def check_date(date_str):
    try:
        datetime.strptime(date_str, "%m.%d.%Y")
        return True
    except ValueError:
        return False
    except TypeError:
        return False


def create_profile(connection, data_path):
    connection.create_table(type_="profile")
    # open each workbook and parse the data
    profile_data = os.path.join(data_path, "profile")
    # create a insert query template
    insert_query = """INSERT INTO profile VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
    # create a main loop for file processing
    for file_name in os.listdir(profile_data):
        file = os.path.join(profile_data, file_name)
        data = xlrd.open_workbook(file)
        sheet = data.sheet_by_index(0)

        labels = ["Identity Number", "Date of Birth", "Gender", "Employed By", "Issue Date", "Education",
                  "Children", "Family", "Marital Status", "Position", "Housing", "Income"]
        values = [None for _ in range(len(labels))]
        row = sheet.nrows
        column = sheet.ncols
        for i in range(row):
            for j in range(column):
                for k in range(len(labels)):
                    if sheet.cell(i, j).value == labels[k]:
                        if labels[k] in ("Date of Birth", "Issue Date"):
                            if check_date(sheet.cell(i + 1, j).value):
                                values[k] = sheet.cell(i + 1, j).value
                            else:
                                temp = datetime.fromordinal(int(sheet.cell(i + 1, j).value))
                                temp = datetime(day=temp.day, month=temp.month, year=temp.year + 1900)
                                temp = temp.strftime("%m.%d.%Y")
                                values[k] = temp
                        else:
                            values[k] = sheet.cell(i + 1, j).value
        connection.cursor.execute(insert_query, values)
    connection.connection.commit()


def create_contract(connection, data_path):
    connection.create_table(type_="contract")
    # open each workbook and parse the data
    profile_data = os.path.join(data_path, "contracts")
    # create a insert query template
    insert_query = """INSERT INTO contract VALUES (?, ?, ?, ?, ?, ?)"""
    for file_name in os.listdir(profile_data):
        file = os.path.join(profile_data, file_name)
        data = xlrd.open_workbook(file)
        sheet = data.sheet_by_index(0)
        labels = ['Identity Number', 'Contract Number', 'Amount', 'Type', 'Term (month)', 'Annuity']
        values = [None for _ in range(len(labels))]
        row = sheet.nrows
        column = sheet.ncols
        for i in range(row):
            for j in range(column):
                for k in range(len(labels)):
                    if sheet.cell(i, j).value == labels[k]:
                        values[k] = sheet.cell(i + 1, j).value
        connection.cursor.execute(insert_query, values)
    connection.connection.commit()


def create_payments(connection, data_path):
    connection.create_table(type_="payment")
    insert_query = """INSERT INTO payment VALUES (?, ?, ?, ?)"""
    excel = xlrd.open_workbook(data_path)
    sheet = excel.sheet_by_index(0)
    data = [sheet.col_values(0)[1::], sheet.col_values(1)[1::], sheet.col_values(2)[1::], sheet.col_values(3)[1::]]
    for data in zip(sheet.col_values(0)[1::], sheet.col_values(1)[1::], sheet.col_values(2)[1::],
                    sheet.col_values(3)[1::]):
        values = [None, None, None, None]
        if check_date(data[1]):
            values[1] = data[1]
        else:
            temp = datetime.fromordinal(int(data[1]))
            temp = datetime(day=temp.day, month=temp.month, year=temp.year + 1900)
            temp = temp.strftime("%m.%d.%Y")
            values[1] = temp
        values[0] = int(data[0])
        values[2] = float(data[2])
        values[3] = float(data[3])
        connection.cursor.execute(insert_query, values)
    connection.connection.commit()


def compute_delay_v2(connection):
    param_set = lambda x: "Default" if x > 90 else "Non-Default"
    connection.create_table(type_="payment_delay")
    select_clients = """SELECT contract_id, issue_date, payment_date FROM profile_contract_payment"""
    insert_values = """INSERT INTO payment_delay VALUES (?, ?, ?, ?, ?, ?)"""
    data = connection.cursor.execute(select_clients).fetchall()
    data = [(item[0], datetime.strptime(item[1], "%m.%d.%Y"), datetime.strptime(item[2], "%m.%d.%Y")) for item in data]
    data = pd.DataFrame(data, columns=["contract_id", "issue_date", "payment_date"]).groupby("contract_id")
    for name, group in data:
        temp = group.sort_values(by="payment_date", ascending=True).copy()
        for curr, nxt in zip(temp["payment_date"], temp["payment_date"][1:]):
            delta = nxt - curr
            connection.cursor.execute(insert_values, (name, curr.strftime("%m.%d.%Y"), nxt.strftime("%m.%d.%Y"), delta.days, param_set(delta.days), (temp["payment_date"].iloc[0] - temp["issue_date"].iloc[0]).days))
    connection.connection.commit()


def compute_delay_v3(connection):
    connection.create_table(type_="payment_delay")
    select_clients = """SELECT contract_id, payment_date, amount_due, amount_paid FROM payment"""
    insert_query = """INSERT INTO payment_delay VALUES (?, ?, ?, ?)"""
    data = connection.cursor.execute(select_clients).fetchall()
    data = [(item[0], datetime.strptime(item[1], "%m.%d.%Y"), item[2], item[3]) for item in data]
    data = pd.DataFrame(data, columns=["contract_id", "payment_date",
                                       "amount_due", "amount_paid"]).groupby("contract_id")
    for name, group in data:
        temp = group.sort_values(by="payment_date", ascending=True).copy()
        temp.reset_index(inplace=True)
        temp["diff"] = temp["payment_date"].diff().dt.days.fillna(0)
        temp["payment_flag"] = (temp['amount_due'] > temp['amount_paid']).astype(int)
        flag = 0
        delay = 0
        bin_flag = False
        for index, row in temp.iterrows():
            if row["payment_flag"]:
                delay += row["diff"] if bin_flag else 0
                flag += 1
                bin_flag = True
            else:
                delay = row["diff"]
                flag = 0
                bin_flag = False
            if flag >= 4:
                connection.cursor.execute(insert_query, [name, row["payment_date"].strftime("%m.%d.%Y"),
                                                         delay, "Default"])
            else:
                connection.cursor.execute(insert_query, [name, row["payment_date"].strftime("%m.%d.%Y"),
                                                         delay, "Non-Default"])
    connection.connection.commit()


def check_input(string):
    if '"' in string:
        return string, "str"
    elif "'" in string:
        return string, "str"
    else:
        try:
            return int(string), "int"
        except ValueError:
            print("Values is not int")
            try:
                return float(string), "float"
            except ValueError:
                print("Value is not float")


def generate_range(strat_date, end_date, horizon):
    points = [strat_date]
    while points[-1] < end_date:
        new_date = points[-1] + timedelta(days=horizon)
        points.append(new_date)
    return points


def write_dataframe(dataframe, connection, sql_template):
    for _, row in dataframe.iterrows():
        connection.cursor.execute(sql_template, [i for i in row])
    connection.connection.commit()


def resample_frame(df, days, key):
    df = df.set_index(key)
    return df.resample('%sD' % str(days))


def search_engine(data):
    search = input("Enter parameter for filtering resulting values (Format 'column_name') _>")
    if search not in data.columns:
        print("Can't find column")
        return 0, 0, 0
    good_data = data[data["status"] == "Non-Default"].copy()
    bad_data = data[data["status"] == "Default"].copy()
    return good_data, bad_data, search


def WOE(good, bad):
    try:
        return np.log(good / bad)
    except ZeroDivisionError:
        return 0


def IV(good, bad):
    return np.sum(good - bad) * WOE(good, bad)


def smart_drow(bad_data, good_data, key):
    if bad_data.empty or good_data.empty:
        print("No Data")
        return 0
    # setup switch
    if key == "gender":
        # думаю сюда можно добавлять и другие фичи
        # получаем значени для каждой из групп для выбранного ключа т.е.
        # для bad_values и gender это будет [количест-во мужчит с дефолтом, количество женщин с дефолтом]
        bad_value = bad_data.groupby(key).describe().iloc[:, 0].values
        good_value = good_data.groupby(key).describe().iloc[:, 0].values
        x_value = bad_data.groupby(key).describe().iloc[:, 0].index.values
        woe_value = WOE(good_value, bad_value)
        iv_value = IV(good_value, bad_value)
        print("WOE=%s" % str(woe_value))
        print("IV=%s" % str(iv_value))
        fig, ax = plt.subplots()
        for i in range(len(x_value)):
            ax.vlines(x=x_value[i], ymin=-0.5, ymax=woe_value[i], linestyle="dashed")
            ax.hlines(y=woe_value[i], xmin=-0.5, xmax=x_value[i], linestyle="dashed")
        ax.scatter(x_value, woe_value, c="red", marker="o")
        for i, value in enumerate(zip(x_value, woe_value)):
            ax.annotate("(%.2f, %.2f)" % (value[0], value[1]), (x_value[i], woe_value[i] + 0.3))
        plt.xlim(-0.5, 1.5)
        plt.ylim(0, 10)
        plt.xlabel("gender")
        plt.ylabel("WOE")
        plt.grid()
        plt.title("WOE/IV Chart \n IV = %.2f (for male) IV = %2.f (for female)" % (iv_value[0], iv_value[1]))
        plt.tight_layout()
        plt.savefig("images/%s.png" % key, dpi=150)
    if key == "amount_due":
        bad_value = bad_data[key].count()
        good_value = good_data[key].count()
        print(roc_curve(good_value, bad_value))


def interface(connection):
    print("+" + "=" * 20 + " WELCOME " + "=" * 20 + "+")
    correct = False
    # цикл пока не будет введен верный ответ
    while not correct:
        horizon = input("Enter the horizon of risk (Format is a int value i.e. count of days) _> ")
        try:
            horizon = int(horizon)
            if horizon < 90:
                print("You entered >%s<. Make sure that it's equal to required format" % horizon)
            else:
                correct = True
        except ValueError:
            print("You entered >%s<. Make sure that it's equal to required format" % horizon)
    # ищем клиентов с просрочкой более 90 + и джойним большую таблицу
    select_query = """SELECT * FROM payment_delay as PD JOIN profile_contract_payment as PCP ON PCP.contract_id = 
    PD.contract_id AND PCP.payment_date = PD.payment_date"""
    connection.cursor.execute(select_query)
    data = []
    # в будущем строки ниже облегчат жизнь
    for row in connection.cursor.fetchall():
        contract_id = row[0]
        payment_date = datetime.strptime(row[1], "%m.%d.%Y")
        payment_delay = row[2]
        status = row[3]
        id_ = row[4]
        birth = datetime.strptime(row[5], "%m.%d.%Y")
        gender = int(row[6])
        employed_by = row[7]
        issue_date = datetime.strptime(row[8], "%m.%d.%Y")
        education = int(row[9])
        children = row[10]
        family = row[11]
        material_status = row[12]
        position = row[13]
        housing = row[14]
        income = row[15]
        amount = row[18]
        type_ = row[19]
        month_term = row[20]
        annuity = row[21]
        amount_due = row[24]
        amount_paid = row[25]
        # добавляем в список в нужном порядке
        data.append([id_, contract_id, birth, gender, employed_by, issue_date, education, children, family,
                     material_status, position, housing, income, amount, type_, month_term, annuity, payment_date,
                     amount_due, amount_paid, payment_delay, status])
    data = pd.DataFrame(data, columns=["id_", "contract_id", "birth", "gender", "employed_by", "issue_date",
                                       "education", "children", "family", "material_status", "position", "housing",
                                       "income", "amount", "type_", "month_term", "annuity", "payment_date",
                                       "amount_due", "amount_paid", "payment_delay", "status"],
                        )

    # выводим сообщение если таких клиентов не нашлось
    if data[data["payment_delay"] > 90].empty:
        print("No clients with payment_delay > 90")
        # выходим из программы
        return 0
    else:
        # иначе печатаем
        print(tabulate(data[data["payment_delay"] > 90][["contract_id",
                                                         "payment_date",
                                                         "payment_delay",
                                                         "gender",
                                                         "income"]],
                       headers='keys', tablefmt='psql'))
    # я разбиваю всех плохих на группы по N дней потом считаю количесво записей в каждой из групп и беру среднее
    # округляя вверх
    grouped = data[data["payment_delay"] > 90].groupby(pd.Grouper(key='payment_date', freq='%sD' % str(horizon)))
    print("In your chosen horizon, the risk will be equal ~%s" %
          str(math.ceil(grouped.describe()["contract_id"]["count"].mean())))

    # делаем поиск
    good_data, bad_data, key = search_engine(data)

    # дальше все передаем в функцию а там уже будем все считать и рисовать
    smart_drow(good_data=good_data, bad_data=bad_data, key=key)


def get_age(date):
    try:
        return date.days // 365
    except AttributeError:
        return date.dt.days // 365


def select_peoples(connection):
    def get_stats(group_):
        return {'min': group_.min(), 'max': group_.max(), 'count': group_.count(), 'mean': group_.mean()}
    select_query = """SELECT * FROM payment_delay as PD JOIN profile_contract_payment as PCP ON PCP.contract_id = 
        PD.contract_id AND PCP.payment_date = PD.payment_date"""
    connection.cursor.execute(select_query)
    data = []
    # в будущем строки ниже облегчат жизнь
    for row in connection.cursor.fetchall():
        contract_id = row[0]
        payment_date = datetime.strptime(row[1], "%m.%d.%Y")
        payment_delay = row[2]
        status = row[3]
        id_ = row[4]
        birth = datetime.strptime(row[5], "%m.%d.%Y")
        gender = int(row[6])
        employed_by = row[7]
        issue_date = datetime.strptime(row[8], "%m.%d.%Y")
        education = int(row[9])
        children = row[10]
        family = row[11]
        material_status = row[12]
        position = row[13]
        housing = row[14]
        income = row[15]
        amount = row[18]
        type_ = row[19]
        month_term = row[20]
        annuity = row[21]
        amount_due = row[24]
        amount_paid = row[25]
        # добавляем в список в нужном порядке
        data.append([id_, contract_id, birth, gender, employed_by, issue_date, education, children, family,
                     material_status, position, housing, income, amount, type_, month_term, annuity, payment_date,
                     amount_due, amount_paid, payment_delay, status])
    data = pd.DataFrame(data, columns=["id_", "contract_id", "birth", "gender", "employed_by", "issue_date",
                                       "education", "children", "family", "material_status", "position", "housing",
                                       "income", "amount", "type_", "month_term", "annuity", "payment_date",
                                       "amount_due", "amount_paid", "payment_delay", "status"],
                        )
    if data.empty:
        print("Problem with data")
        return 0

    grouped = data.groupby(pd.Grouper(key='payment_date', freq='Y'))
    # считаем года по дню рождения
    data["age"] = get_age((datetime.now() - data["birth"]))
    values = {}
    for age, group in data.groupby("age"):
        good_data = group[group["status"] == "Non-Default"].copy()
        bad_data = group[group["status"] == "Default"].copy()
        metric = WOE(good_data.shape[0], bad_data.shape[0])
        values[age] = metric
    print(values)
    data["metric"] = data["age"].map(values)
    bins = np.arange(data["metric"].min() - 0.5 * data["metric"].max(), data["metric"].max() + 0.5 * data["metric"].max(), data["metric"].std())
    labels = []
    for i in range(bins.size - 1):
        labels.append("Group WOE [%.2f, %.2f]" % (bins[i], bins[i + 1]))
    print(labels)
    result = data["age"].groupby(pd.cut(data["metric"], bins, labels=labels)).apply(get_stats).unstack().fillna(0)
    print(tabulate(result, headers="keys", tablefmt="psql"))

