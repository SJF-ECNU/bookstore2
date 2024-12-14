import logging
import os
import pymysql
import threading

class Store:
    database: str
    connection: pymysql.connections.Connection
    cursor: pymysql.cursors.DictCursor

    def __init__(self, db_host="localhost", db_user="root", db_password="040708", db_name="bookstore"):
        try:
            # 连接 MySQL 数据库
            self.connection = pymysql.connect(
                host=db_host,
                user=db_user,
                password=db_password,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            self.cursor = self.connection.cursor()
            
            # 创建数据库(如果不存在)
            self.cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
            self.cursor.execute(f"USE {db_name}")
            
            # 初始化表
            self.init_tables()
            
        except pymysql.Error as e:
            logging.error(f"Error connecting to database: {e}")
            raise

    def init_tables(self):
        try:
            # 删除已存在的表（如果需要重新创建）
            self.cursor.execute("DROP TABLE IF EXISTS new_order_detail")
            self.cursor.execute("DROP TABLE IF EXISTS new_order")
            self.cursor.execute("DROP TABLE IF EXISTS store")
            self.cursor.execute("DROP TABLE IF EXISTS user_store")
            self.cursor.execute("DROP TABLE IF EXISTS user")

            # 创建用户表
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS user (
                    user_id VARCHAR(255) PRIMARY KEY,
                    password VARCHAR(255) NOT NULL,
                    balance DECIMAL(10,2) DEFAULT 0,
                    token VARCHAR(255),
                    terminal VARCHAR(255)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            # 创建商店表
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_store (
                    store_id VARCHAR(255) PRIMARY KEY,
                    user_id VARCHAR(255),
                    FOREIGN KEY (user_id) REFERENCES user(user_id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            # 创建库存表
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS store (
                    store_id VARCHAR(255),
                    book_id VARCHAR(255),
                    book_info TEXT,
                    stock_level INT DEFAULT 0,
                    PRIMARY KEY (store_id, book_id),
                    FOREIGN KEY (store_id) REFERENCES user_store(store_id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            # 创建订单表
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS new_order (
                    order_id VARCHAR(255) PRIMARY KEY,
                    user_id VARCHAR(255),
                    store_id VARCHAR(255),
                    is_paid BOOLEAN DEFAULT FALSE,
                    is_shipped BOOLEAN DEFAULT FALSE,
                    is_received BOOLEAN DEFAULT FALSE,
                    order_completed BOOLEAN DEFAULT FALSE,
                    status VARCHAR(20) DEFAULT 'pending',
                    created_time DATETIME,
                    FOREIGN KEY (user_id) REFERENCES user(user_id) ON DELETE CASCADE,
                    FOREIGN KEY (store_id) REFERENCES user_store(store_id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            # 创建订单详情表
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS new_order_detail (
                    order_id VARCHAR(255),
                    book_id VARCHAR(255),
                    count INT,
                    price DECIMAL(10,2),
                    PRIMARY KEY (order_id, book_id),
                    FOREIGN KEY (order_id) REFERENCES new_order(order_id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            
            self.connection.commit()

        except pymysql.Error as e:
            logging.error(f"Error initializing tables: {e}")
            raise

    def get_db_conn(self):
        # 返回 MySQL 数据库连接实例
        return self.connection

    @property
    def db(self):
        return self.connection

# 全局数据库实例
database_instance: Store = None
# 数据库初始化同步的全局变量
init_completed_event = threading.Event()

def init_database(db_host, db_user, db_password, db_name):
    global database_instance
    database_instance = Store(db_host, db_user, db_password, db_name)
    init_completed_event.set()

def get_db_conn():
    global database_instance
    return database_instance.get_db_conn()
