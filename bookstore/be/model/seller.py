import mysql.connector
from be.model import error
from be.model import db_conn

class Seller(db_conn.DBConn):
    def __init__(self):
        db_conn.DBConn.__init__(self)

    def add_book(
        self,
        user_id: str,
        store_id: str,
        book_id: str,
        book_json_str: str,
        stock_level: int,
    ):
        try:
            # 检查用户是否存在
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            # 检查商店是否存在
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id)
            # 检查书籍是否已经存在
            if self.book_id_exist(store_id, book_id):
                return error.error_exist_book_id(book_id)

            # 将书籍插入到store表中
            query = """
                INSERT INTO store (store_id, book_id, book_info, stock_level) 
                VALUES (%s, %s, %s, %s)
            """
            self.cursor.execute(query, (store_id, book_id, book_json_str, stock_level))
            self.conn.commit()
        except Exception as e:
            return 530, "{}".format(str(e))
        return 200, "ok"

    def add_stock_level(
        self, 
        user_id: str, 
        store_id: str, 
        book_id: str, 
        add_stock_level: int
    ):
        try:
            # 检查用户、商店和书籍是否存在
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id)
            if not self.book_id_exist(store_id, book_id):
                return error.error_non_exist_book_id(book_id)

            # 更新库存数量
            query = """
                UPDATE store 
                SET stock_level = stock_level + %s 
                WHERE store_id = %s AND book_id = %s
            """
            self.cursor.execute(query, (add_stock_level, store_id, book_id))
            self.conn.commit()
        except Exception as e:
            return 530, "{}".format(str(e))
        return 200, "ok"

    def create_store(self, user_id: str, store_id: str) -> (int, str): 
        try:
            # 检查用户是否存在
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            # 检查商店是否已经存在
            if self.store_id_exist(store_id):
                return error.error_exist_store_id(store_id)

            # 创建商店，插入到user_store表中
            query = """
                INSERT INTO user_store (store_id, user_id) 
                VALUES (%s, %s)
            """
            self.cursor.execute(query, (store_id, user_id))
            self.conn.commit()
        except Exception as e:
            return 530, "{}".format(str(e))
        return 200, "ok"

    def ship(
            self,
            user_id: str,
            store_id: str,
            order_id: str,
            ):
        try:
            # 检查用户是否存在
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            # 检查商店是否存在
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id)
            # 检查订单是否存在
            if not self.order_id_exist(order_id):
                return error.error_invalid_order_id(order_id)
            # 检查订单是否已经支付
            if not self.order_is_paid(order_id):
                return error.error_not_be_paid(order_id)
            # 检查订单是否已经发货
            if self.order_is_shipped(order_id):
                return error.error_order_is_shipped(order_id)

            # 更新订单状态
            query = """
                UPDATE new_order 
                SET is_shipped = 1 
                WHERE order_id = %s AND store_id = %s
            """
            self.cursor.execute(query, (order_id, store_id))
            self.conn.commit()
        
        except Exception as e:
            return 520, "{}".format(str(e))
        return 200, "ok"

    def query_one_store_orders(self, user_id: str, store_id: str, password) -> (int, str, list): 
        try:
            # 检查用户与商店是否存在
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id) + ("None",)
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id) + ("None",)

            # 检查用户密码是否正确
            query = "SELECT password FROM user WHERE user_id = %s"
            self.cursor.execute(query, (user_id,))
            user = self.cursor.fetchone()
            if user is None or user[0] != password:  # user[0] 是 password 字段
                return error.error_authorization_fail() + ("None",)

            # 查找用户是否存在该商店
            query = "SELECT * FROM user_store WHERE user_id = %s AND store_id = %s"
            self.cursor.execute(query, (user_id, store_id))
            user_store = self.cursor.fetchone()

            if not user_store:
                return error.error_no_store_found(user_id) + ("None",)

            # 查找该商店的所有订单
            query = "SELECT * FROM new_order WHERE store_id = %s"
            self.cursor.execute(query, (store_id,))
            orders = self.cursor.fetchall()

        except Exception as e:
            return 530, "{}".format(str(e)), "None"
        return 200, "ok", str(orders)

    def query_all_store_orders(self, user_id: str, password) -> (int, str, list): 
        try:
            # 检查用户是否存在
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id) + ("None",)

            # 检查用户密码是否正确
            query = "SELECT password FROM user WHERE user_id = %s"
            self.cursor.execute(query, (user_id,))
            user = self.cursor.fetchone()
            if user is None or user[0] != password:  # user[0] 是 password 字段
                return error.error_authorization_fail() + ("None",)

            # 查找用户的商店
            query = "SELECT * FROM user_store WHERE user_id = %s"
            self.cursor.execute(query, (user_id,))
            user_stores = self.cursor.fetchall()

            # 检查是否有商店
            if len(user_stores) == 0:
                return error.error_no_store_found(user_id) + ("None",)

            all_store_orders = {}
            for user_store in user_stores:
                store_id = user_store[0]  # user_store[0] 是 store_id 字段
                # 查找该商店的所有订单
                query = "SELECT * FROM new_order WHERE store_id = %s"
                self.cursor.execute(query, (store_id,))
                orders = self.cursor.fetchall()
                all_store_orders[store_id] = orders

        except Exception as e:
            return 530, "{}".format(str(e)), "None"
        return 200, "ok", str(all_store_orders)
