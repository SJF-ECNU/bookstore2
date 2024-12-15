import logging
import os
import mysql.connector
import threading
from mysql.connector import Error

class Store:
    def __init__(self, db_url="localhost", db_name="bookstore", user="root", password="040708"):
        # 连接 MySQL 数据库
        try:
            self.conn = mysql.connector.connect(
                host=db_url,
                user=user,
                password=password,
                database=db_name
            )
            if self.conn.is_connected():
                self.cursor = self.conn.cursor(dictionary=True)  # 使用字典形式的游标
                self.init_tables()
        except Error as e:
            logging.error(f"Error while connecting to MySQL: {e}")

    def init_tables(self):
        try:
            # 初始化 MySQL 表
            self.create_table_user()
            self.create_table_user_store()
            self.create_table_store()
            self.create_table_new_order()
            self.create_table_new_order_detail()

        except Error as e:
            logging.error(e)

    def create_table_user(self):
        # 创建 user 表
        query = """
        CREATE TABLE IF NOT EXISTS user (
            user_id VARCHAR(255) PRIMARY KEY,
            password VARCHAR(255) NOT NULL,
            balance DECIMAL(10, 2) DEFAULT 0,
            token TEXT NOT NULL, 
            terminal VARCHAR(255) NOT NULL
        )
        """
        self.cursor.execute(query)
        self.conn.commit()

    def create_table_user_store(self):
        # 创建 user_store 表
        query = """
        CREATE TABLE IF NOT EXISTS user_store (
            user_id VARCHAR(255),
            store_id VARCHAR(255),
            PRIMARY KEY (user_id, store_id),
            FOREIGN KEY (user_id) REFERENCES user(user_id)
        )
        """
        self.cursor.execute(query)
        self.conn.commit()

    def create_table_store(self):
        # 创建 store 表
        query = """
        CREATE TABLE IF NOT EXISTS store (
            store_id VARCHAR(255),
            book_id VARCHAR(255),
            stock_level INT NOT NULL,
            book_info TEXT,
            PRIMARY KEY (store_id, book_id)
        )
        """
        self.cursor.execute(query)
        self.conn.commit()

    def create_table_new_order(self):
        # 创建 new_order 表
        query = """
        CREATE TABLE IF NOT EXISTS new_order (
            order_id VARCHAR(255) PRIMARY KEY,
            store_id VARCHAR(255),
            user_id VARCHAR(255),
            is_paid BOOLEAN DEFAULT FALSE,
            is_shipped BOOLEAN DEFAULT FALSE,
            is_received BOOLEAN DEFAULT FALSE,
            order_completed BOOLEAN DEFAULT FALSE,
            status VARCHAR(50),
            created_time DATETIME,
            FOREIGN KEY (store_id) REFERENCES user_store(store_id),
            FOREIGN KEY (user_id) REFERENCES user(user_id)
        )
        """
        self.cursor.execute(query)
        self.conn.commit()

    def create_table_new_order_detail(self):
        # 创建 new_order_detail 表
        query = """
        CREATE TABLE IF NOT EXISTS new_order_detail (
            order_id VARCHAR(255),
            book_id VARCHAR(255),
            count INT NOT NULL,
            price DECIMAL(10, 2) NOT NULL,
            PRIMARY KEY (order_id, book_id),
            FOREIGN KEY (order_id) REFERENCES new_order(order_id)
        )
        """
        self.cursor.execute(query)
        self.conn.commit()

    def get_db_conn(self):
        # 返回 MySQL 数据库连接
        return self.conn

# 全局数据库实例
database_instance: Store = None
# 数据库初始化同步的全局变量
init_completed_event = threading.Event()

def init_database(db_url, db_name, db_user, db_password):
    global database_instance
    database_instance = Store(db_url, db_name, db_user, db_password)
    init_completed_event.set()

def get_db_conn():
    global database_instance
    return database_instance.get_db_conn()