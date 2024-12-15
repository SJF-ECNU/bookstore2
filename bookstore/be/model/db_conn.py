import mysql.connector
from mysql.connector import Error

class DBConn:
    def __init__(self):
        # 连接MySQL
        try:
            self.conn = mysql.connector.connect(
                host="localhost",
                user="root",
                password="040708",
                database="bookstore"
            )
            if self.conn.is_connected():
                # 使用字典形式返回查询结果
                self.cursor = self.conn.cursor(dictionary=True)
        except Error as e:
            print("Error while connecting to MySQL", e)

    def user_id_exist(self, user_id):
        # 查询user表中是否存在给定user_id
        query = "SELECT * FROM user WHERE user_id = %s"
        self.cursor.execute(query, (user_id,))
        user = self.cursor.fetchone()
        return user is not None

    def book_id_exist(self, store_id, book_id):
        # 查询store表中是否存在对应的store_id和book_id
        query = "SELECT * FROM store WHERE store_id = %s AND book_id = %s"
        self.cursor.execute(query, (store_id, book_id))
        store = self.cursor.fetchone()
        return store is not None

    def store_id_exist(self, store_id):
        # 查询user_store表中是否存在给定store_id
        query = "SELECT * FROM user_store WHERE store_id = %s"
        self.cursor.execute(query, (store_id,))
        user_store = self.cursor.fetchone()
        return user_store is not None

    def order_id_exist(self, order_id):
        # 查询new_order表中是否存在给定order_id
        query = "SELECT * FROM new_order WHERE order_id = %s"
        self.cursor.execute(query, (order_id,))
        order = self.cursor.fetchone()
        return order is not None

    def order_is_paid(self, order_id):
        # 查询order是否被支付
        query = "SELECT is_paid FROM new_order WHERE order_id = %s"
        self.cursor.execute(query, (order_id,))
        order = self.cursor.fetchone()
        return order["is_paid"] if order else False  # 返回字典中的值

    def order_is_shipped(self, order_id):
        # 查询order是否被发货
        query = "SELECT is_shipped FROM new_order WHERE order_id = %s"
        self.cursor.execute(query, (order_id,))
        order = self.cursor.fetchone()
        return order["is_shipped"] if order else False  # 返回字典中的值

    def close(self):
        # 关闭数据库连接
        if self.conn.is_connected():
            self.cursor.close()
            self.conn.close()