import mysql.connector

class DBConn:
    def __init__(self):
        # 连接MySQL数据库
        self.conn = mysql.connector.connect(
            host="root",  # MySQL用户名
            password="040708",  # MySQL密码
            database="bookstore"  # 使用bookstore数据库
        )
        self.cursor = self.conn.cursor(dictionary=True)  # 使用字典模式获取查询结果
    
    def user_id_exist(self, user_id):
        # 查询user表中是否存在给定user_id
        self.cursor.execute("SELECT * FROM user WHERE user_id = %s", (user_id,))
        user = self.cursor.fetchone()
        if user is None:
            return False
        return True
    
    def book_id_exist(self, store_id, book_id):
        # 查询store表中是否存在对应的store_id和book_id
        self.cursor.execute("SELECT * FROM store WHERE store_id = %s AND book_id = %s", (store_id, book_id))
        store = self.cursor.fetchone()
        if store is None:
            return False
        return True

    def store_id_exist(self, store_id):
        # 查询user_store表中是否存在给定store_id
        self.cursor.execute("SELECT * FROM user_store WHERE store_id = %s", (store_id,))
        user_store = self.cursor.fetchone()
        if user_store is None:
            return False
        return True
    
    def order_id_exist(self, order_id):
        # 查询new_order表中是否存在给定order_id
        self.cursor.execute("SELECT * FROM new_order WHERE order_id = %s", (order_id,))
        order = self.cursor.fetchone()
        if order is None:
            return False
        return True
    
    def order_is_paid(self, order_id):
        # 查询order是否被支付
        self.cursor.execute("SELECT is_paid FROM new_order WHERE order_id = %s", (order_id,))
        order = self.cursor.fetchone()
        if order and order['is_paid'] == 0:  # 0 表示未支付，1表示已支付
            return False
        return True
    
    def order_is_shipped(self, order_id):
        # 查询order是否被发货
        self.cursor.execute("SELECT is_shipped FROM new_order WHERE order_id = %s", (order_id,))
        order = self.cursor.fetchone()
        if order and order['is_shipped'] == 0:  # 0 表示未发货，1表示已发货
            return False
        return True
    
    def close(self):
        # 关闭数据库连接
        self.cursor.close()
        self.conn.close()
