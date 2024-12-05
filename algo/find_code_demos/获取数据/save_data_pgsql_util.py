import os
import psycopg2
from psycopg2 import sql
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, JSON, TIMESTAMP, text
from sqlalchemy.dialects.postgresql import insert
from dotenv import load_dotenv

class PostgreSQLDatabase:
    def __init__(self, user, password, host, port, dbname="postgres"):
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.dbname = dbname
        self.connection = None
        self.cursor = None

    def connect(self):
        try:
            self.connection = psycopg2.connect(
                dbname=self.dbname,
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port
            )
            self.cursor = self.connection.cursor()
            print(f"Connected to '{self.dbname}' database")
        except Exception as error:
            print(f"Error while connecting to '{self.dbname}' database", error)

    def close(self):
        if self.connection:
            self.cursor.close()
            self.connection.close()
            print("PostgreSQL connection is closed")

    def execute_query(self, query, params=None):
        try:
            self.cursor.execute(query, params)
            self.connection.commit()
            return self.cursor.fetchall()
        except Exception as error:
            print("Error executing query", error)
            self.connection.rollback()
            return None

    def create_database_if_not_exists(self, dbname):
        try:
            self.connect()
            self.cursor.execute(sql.SQL("SELECT 1 FROM pg_database WHERE datname = %s"), [dbname])
            exists = self.cursor.fetchone()
            
            if not exists:
                self.cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(dbname)))
                print(f"Database '{dbname}' created successfully")
            else:
                print(f"Database '{dbname}' already exists")
        except Exception as error:
            print("Error while checking/creating database", error)
        finally:
            self.close()

    def connect_to_database(self, dbname):
        self.dbname = dbname
        self.connect()

    def create_tables(self, table_definitions):
        try:
            self.connect()
            for table_name, table_definition in table_definitions.items():
                create_table_query = sql.SQL("CREATE TABLE IF NOT EXISTS {} ({});").format(
                    sql.Identifier(table_name),
                    sql.SQL(', ').join(map(sql.SQL, table_definition))
                )
                self.cursor.execute(create_table_query)
                self.connection.commit()
                print(f"Table '{table_name}' created successfully")
        except Exception as error:
            print("Error while creating tables", error)
        finally:
            self.close()

# 使用示例
load_dotenv()

user = os.getenv("PG_USER")
password = os.getenv("PG_PASSWORD")
host = os.getenv("PG_HOST")
port = os.getenv("PG_PORT")
dbname = os.getenv("PG_DBNAME")

# 创建数据库类实例
db = PostgreSQLDatabase(user, password, host, port, dbname)