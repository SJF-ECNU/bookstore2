import pymysql
import logging

class DBConn:
    def __init__(self):
        self.conn = None
        self.cursor = None
        try:
            # 连接MySQL数据库
            self.conn = pymysql.connect(
                host="localhost",
                user="root",
                password="040708",
                database="bookstore",
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            self.cursor = self.conn.cursor()
        except pymysql.Error as e:
            logging.error(f"数据库连接失败: {e}")
            raise

    def user_id_exist(self, user_id):
        self.cursor.execute("SELECT user_id FROM user WHERE user_id = %s", (user_id,))
        row = self.cursor.fetchone()
        return row is not None

    def book_id_exist(self, store_id, book_id):
        self.cursor.execute(
            "SELECT book_id FROM store WHERE store_id = %s AND book_id = %s",
            (store_id, book_id)
        )
        row = self.cursor.fetchone()
        return row is not None

    def store_id_exist(self, store_id):
        self.cursor.execute("SELECT store_id FROM user_store WHERE store_id = %s", (store_id,))
        row = self.cursor.fetchone()
        return row is not None
    
    def order_id_exist(self, order_id):
        self.cursor.execute("SELECT order_id FROM new_order WHERE order_id = %s", (order_id,))
        row = self.cursor.fetchone()
        return row is not None
    
    def order_is_paid(self, order_id):
        self.cursor.execute("SELECT is_paid FROM new_order WHERE order_id = %s", (order_id,))
        row = self.cursor.fetchone()
        return row is not None and row['is_paid']
    
    def order_is_shipped(self, order_id):
        self.cursor.execute("SELECT is_shipped FROM new_order WHERE order_id = %s", (order_id,))
        row = self.cursor.fetchone()
        return row is not None and row['is_shipped']

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
