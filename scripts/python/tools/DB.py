#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/6/1
# @Author  : KeJun.Chen
# @File    : DB.py
# @Email   : kejun.chen@amlogic.com
# @Ide: PyCharm
import logging
import pymysql
import pytest


class DB:
    def __init__(self):
        self.connection = None
        self.cursor = None

    def __enter__(self):
        # Create a database connection
        try:
            self.connection = pymysql.connect(
                host="10.18.11.98",
                user="AutoTest",
                password="Linux2017!",
                database="AutoTest"
            )
            # Create a cursor object
            self.cursor = self.connection.cursor()
        except pymysql.err.OperationalError as err:
            logging.info("Failed to establish MySQL connection.")
            print("Failed to establish MySQL connection.")

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Close the cursor and connection
        if self.cursor:
            self.cursor.close()
        if self.connection and self.connection.open:
            self.connection.close()
            logging.info('MySQL connection closed.')

    def insert_data_field(self, table_name, field_names, values):
        try:
            insert_query = f"INSERT INTO {table_name} ({', '.join(field_names)}) VALUES ({', '.join(['%s'] * len(field_names))})"
            logging.debug(f'insert_query: {insert_query}')
            self.cursor.executemany(insert_query, values)
            self.connection.commit()
            logging.info("Data inserted successfully into the database.")
        except pymysql.Error as error:
            logging.error("MySQL错误：%s", error)

    def insert_data_row(self, table_name, *values):
        try:
            # Get the field names from the table
            field_names = self.get_table_fields(table_name)

            # Remove ID and UPDATE_TIME from the field names
            field_names = [field for field in field_names if field != 'ID' and field != 'UPDATE_TIME']
            logging.debug(f'field_names: {field_names}')

            # Create the INSERT query with placeholders for the values
            insert_query = f"INSERT INTO {table_name} ({', '.join(field_names)}) VALUES ({', '.join(['%s'] * len(field_names))})"
            logging.debug(f'insert_query: {insert_query}')

            # Check if the number of provided values matches the number of fields
            if len(values) == len(field_names):
                # Execute the INSERT query with the values
                self.cursor.execute(insert_query, values)
                self.connection.commit()
                logging.info("Data inserted successfully into the database.")
            else:
                logging.error("Number of values doesn't match the number of fields.")
        except pymysql.Error as error:
            logging.error("MySQL Error: %s", error)

    def insert_kpi_data(self, table_name, flag, *values):
        try:
            # Get the field names from the table
            field_names = self.get_table_fields(table_name)

            # Remove ID and UPDATE_TIME from the field names
            field_names = [field for field in field_names if field != 'ID' and field != 'UPDATE_TIME']
            logging.debug(f'field_names: {field_names}')

            # Create the INSERT query with placeholders for the values
            insert_query = f"INSERT INTO {table_name} ({', '.join(field_names)}) VALUES ({', '.join(['%s'] * len(field_names))})"
            logging.debug(f'insert_query: {insert_query}')

            # Check if the number of provided values matches the number of fields
            if len(values) + 1 == len(field_names):
                # Execute the INSERT query with the values
                # self.cursor.execute(insert_query, values)
                self.cursor.execute(insert_query, (*values, flag))
                self.connection.commit()
                logging.info("Data inserted successfully into the database.")
            else:
                logging.error("Number of values doesn't match the number of fields.")
        except pymysql.Error as error:
            logging.error("MySQL Error: %s", error)

    def get_table_fields(self, table_name):
        # Retrieve the field names from the database for the specified table
        field_names = []
        try:
            query = f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table_name}' ORDER BY ORDINAL_POSITION"
            self.cursor.execute(query)
            result = self.cursor.fetchall()
            field_names = [row[0] for row in result]
        except pymysql.Error as error:
            logging.error("MySQL Error: %s", error)
        return field_names

    def db_connection(self):
        return self.connection

    def get_data_fields(self, table_name, field_names=None, condition=None):
        try:
            if field_names is None:
                select_query = f"SELECT * FROM {table_name}"
            else:
                select_query = f"SELECT {', '.join(field_names)} FROM {table_name}"
            if condition:
                select_query += f" WHERE {condition}"
            logging.debug(f'select_query: {select_query}')
            self.cursor.execute(select_query)
            result = self.cursor.fetchall()
            logging.info("成功从数据库中检索数据。")
            return result
        except pymysql.Error as error:
            logging.error("MySQL错误：%s", error)

    def update_data(self, table_name, field_names, values, condition=None):
        try:
            set_values = ', '.join([f"{field} = %s" for field in field_names])
            update_query = f"UPDATE {table_name} SET {set_values} WHERE {condition}"
            logging.debug(f'update_query: {update_query}')

            self.cursor.execute(update_query, values)

            self.connection.commit()
            logging.info("Data updated successfully into the database.")
        except pymysql.Error as error:
            logging.error("MySQL错误：%s", error)


# Usage example
if __name__ == '__main__':
    with DB() as db:
        db.insert_data_row("TEST_RESULTS", "dvb_trunk", "AATS_DVB_FUNC_15_DVB_C_PROGRAM_RECORDING", "kejun.chen", 1, 0, 0, 0, 177.81, "results/2023.05.31_14.24.34/056_AATS_DVB_FUNC_15_DVB_C_PROGRAM_RECORDING_2/AATS_DVB_FUNC_15_DVB_C_PROGRAM_RECORDING.html")
        db.insert_kpi_data("DVB_SCAN_KPI_RESULTS", 5, 1, 1351, 201, 997, 1274, 3829)
        data_to_insert = [('111.ts', 1),
                          ('222.mp4', 1),
                          ('333.trp', 1)]
        field_names = ['VIDEO', 'VERSION']
        db.insert_data_field('COMPATIBILITY', field_names, data_to_insert)
        data = ['111.ts', '222.mp4']
        data_to_insert = [(item,) for item in data]
        print(data_to_insert)
        field_names = ['VIDEO']
        db.insert_data_field('COMPATIBILITY', field_names, data_to_insert)
        results = db.get_data_fields('COMPATIBILITY', field_names, condition='VERSION=1')
        print(results)
        data_to_update = [1, 0]
        field_names = ['PASS', 'STATUS']
        db.update_data('COMPATIBILITY', field_names, data_to_update, condition="VIDEO='http://qa-sh.amlogic.com:8881/chfs/shared/Test_File/Hardware_testing/power_test/4KH264_30.000fps_10.1Mbps_Wetek-Astra-2m.mp4'")