import logging
import mysql.connector
import threading
from mysql.connector import Error

class Store:
    database: str
    conn: mysql.connector.connect
    cursor: mysql.connector.cursor

    def __init__(self, db_url="localhost", db_user="root", db_password="", db_name="bookstore"):
        # 连接 MySQL 数据库
        try:
            self.conn = mysql.connector.connect(
                host=db_url,
                user=db_user,
                password=db_password,
                database=db_name
            )
            self.cursor = self.conn.cursor(dictionary=True)
            self.init_tables()
        except Error as e:
            logging.error(f"Error while connecting to MySQL: {e}")
            raise

    def init_tables(self):
        try:
            # 初始化 MySQL 表
            self.create_table("user", """
                CREATE TABLE IF NOT EXISTS user (
                    user_id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(255) NOT NULL,
                    password VARCHAR(255) NOT NULL
                )
            """)

            self.create_table("user_store", """
                CREATE TABLE IF NOT EXISTS user_store (
                    user_id INT NOT NULL,
                    store_id INT NOT NULL,
                    PRIMARY KEY (user_id, store_id),
                    FOREIGN KEY (user_id) REFERENCES user(user_id),
                    FOREIGN KEY (store_id) REFERENCES store(store_id)
                )
            """)

            self.create_table("store", """
                CREATE TABLE IF NOT EXISTS store (
                    store_id INT AUTO_INCREMENT PRIMARY KEY,
                    book_id INT NOT NULL,
                    book_name VARCHAR(255) NOT NULL
                )
            """)

            self.create_table("new_order", """
                CREATE TABLE IF NOT EXISTS new_order (
                    order_id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    is_paid BOOLEAN NOT NULL DEFAULT FALSE,
                    is_shipped BOOLEAN NOT NULL DEFAULT FALSE,
                    FOREIGN KEY (user_id) REFERENCES user(user_id)
                )
            """)

            self.create_table("new_order_detail", """
                CREATE TABLE IF NOT EXISTS new_order_detail (
                    order_id INT NOT NULL,
                    book_id INT NOT NULL,
                    quantity INT NOT NULL,
                    PRIMARY KEY (order_id, book_id),
                    FOREIGN KEY (order_id) REFERENCES new_order(order_id),
                    FOREIGN KEY (book_id) REFERENCES store(book_id)
                )
            """)

        except Error as e:
            logging.error(f"Error while initializing tables: {e}")
            raise

    def create_table(self, table_name, create_sql):
        try:
            self.cursor.execute(create_sql)
            self.conn.commit()
            logging.info(f"Table '{table_name}' is ready.")
        except Error as e:
            logging.error(f"Error creating table {table_name}: {e}")
    
    def get_db_conn(self):
        # 返回 MySQL 数据库连接实例
        return self.conn

    def close(self):
        # 关闭数据库连接
        if self.conn.is_connected():
            self.cursor.close()
            self.conn.close()

# 全局数据库实例
database_instance: Store = None
# 数据库初始化同步的全局变量
init_completed_event = threading.Event()

def init_database(db_url, db_user, db_password, db_name):
    global database_instance
    database_instance = Store(db_url, db_user, db_password, db_name)
    init_completed_event.set()

def get_db_conn():
    global database_instance
    return database_instance.get_db_conn()
