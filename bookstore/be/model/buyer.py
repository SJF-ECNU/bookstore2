import mysql.connector
from mysql.connector import Error
import uuid
import json
import logging
from be.model import db_conn
from be.model import error
from datetime import datetime, timedelta
import schedule
import time

class Buyer(db_conn.DBConn):
    # 订单状态映射
    ORDER_STATUS = {
        "pending": "待支付",
        "paid": "已支付",
        "shipped": "已发货",
        "received": "已收货",
        "completed": "已完成",
        "canceled": "已取消"
    }

    def __init__(self):
        # 连接 MySQL
        try:
            self.conn = mysql.connector.connect(
                host="localhost",
                user="root",
                password="040708",
                database="bookstore"
            )
            if self.conn.is_connected():
                self.cursor = self.conn.cursor(dictionary=True)
        except Error as e:
            logging.error(f"Error while connecting to MySQL: {e}")

    def user_id_exist(self, user_id):
        # 检查 user_id 是否存在
        query = "SELECT * FROM user WHERE user_id = %s"
        self.cursor.execute(query, (user_id,))
        user = self.cursor.fetchone()
        return user is not None

    def store_id_exist(self, store_id):
        # 检查 store_id 是否存在
        query = "SELECT * FROM user_store WHERE store_id = %s"
        self.cursor.execute(query, (store_id,))
        store = self.cursor.fetchone()
        return store is not None

    def new_order(self, user_id: str, store_id: str, id_and_count: [(str, int)]) -> (int, str, str):
        order_id = ""
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id) + (order_id,)
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id) + (order_id,)

            # 生成订单ID
            uid = "{}_{}_{}".format(user_id, store_id, str(uuid.uuid1()))

            # 遍历每本书籍及其数量
            for book_id, count in id_and_count:
                # 查找书籍库存
                query = "SELECT * FROM store WHERE store_id = %s AND book_id = %s"
                self.cursor.execute(query, (store_id, book_id))
                store_item = self.cursor.fetchone()
                if store_item is None:
                    return error.error_non_exist_book_id(book_id) + (order_id,)

                stock_level = store_item['stock_level']
                book_info = json.loads(store_item['book_info'])
                price = book_info.get("price")

                if stock_level < count:
                    return error.error_stock_level_low(book_id) + (order_id,)

                # 更新库存
                update_query = "UPDATE store SET stock_level = stock_level - %s WHERE store_id = %s AND book_id = %s AND stock_level >= %s"
                self.cursor.execute(update_query, (count, store_id, book_id, count))
                self.conn.commit()

                # 插入订单详情
                insert_query = "INSERT INTO new_order_detail (order_id, book_id, count, price) VALUES (%s, %s, %s, %s)"
                self.cursor.execute(insert_query, (uid, book_id, count, price))

            # 插入订单
            insert_order_query = """
            INSERT INTO new_order (order_id, store_id, user_id, is_paid, is_shipped, is_received, order_completed, status, created_time)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            self.cursor.execute(insert_order_query, (uid, store_id, user_id, False, False, False, False, "pending", datetime.utcnow()))
            self.conn.commit()
            order_id = uid
        except Exception as e:
            logging.error(f"530, {str(e)}")
            return 530, "{}".format(str(e)), ""

        return 200, "ok", order_id

    def pay_to_platform(self, user_id: str, password: str, order_id: str) -> (int, str):
        try:
            # 查找订单
            query = "SELECT * FROM new_order WHERE order_id = %s"
            self.cursor.execute(query, (order_id,))
            order = self.cursor.fetchone()
            if order is None:
                return error.error_invalid_order_id(order_id)

            buyer_id = order['user_id']

            # 检查用户身份
            if buyer_id != user_id:
                return error.error_authorization_fail()

            user_query = "SELECT * FROM user WHERE user_id = %s"
            self.cursor.execute(user_query, (buyer_id,))
            user = self.cursor.fetchone()
            if user is None or user['password'] != password:
                return error.error_authorization_fail()

            # 检查是否已经付款
            if order.get('is_paid', False):
                return error.error_order_is_paid(order_id)

            # 计算订单总价
            query = "SELECT * FROM new_order_detail WHERE order_id = %s"
            self.cursor.execute(query, (order_id,))
            order_details = self.cursor.fetchall()
            total_price = sum(detail['count'] * detail['price'] for detail in order_details)

            if user['balance'] < total_price:
                return error.error_not_sufficient_funds(order_id)

            # 扣除买家的余额
            update_query = "UPDATE user SET balance = balance - %s WHERE user_id = %s AND balance >= %s"
            self.cursor.execute(update_query, (total_price, buyer_id, total_price))

            # 更新订单状态为已付款
            update_order_query = "UPDATE new_order SET is_paid = %s WHERE order_id = %s"
            self.cursor.execute(update_order_query, (True, order_id))
            self.conn.commit()

        except Exception as e:
            return 530, "{}".format(str(e))

        return 200, "ok"

    def confirm_receipt_and_pay_to_seller(self, user_id: str, password: str, order_id: str) -> (int, str):
        try:
            # 查找订单
            query = "SELECT * FROM new_order WHERE order_id = %s"
            self.cursor.execute(query, (order_id,))
            order = self.cursor.fetchone()
            if order is None:
                return error.error_invalid_order_id(order_id)

            buyer_id = order['user_id']

            # 检查用户身份
            if buyer_id != user_id:
                return error.error_authorization_fail()

            user_query = "SELECT * FROM user WHERE user_id = %s"
            self.cursor.execute(user_query, (buyer_id,))
            user = self.cursor.fetchone()
            if user is None or user['password'] != password:
                return error.error_authorization_fail()

            # 检查是否已经付款
            if not order.get('is_paid', False):
                return error.error_not_be_paid(order_id)

            # 检查是否已确认收货
            if order.get('is_received', False):
                return error.error_order_is_confirmed(order_id)

            store_id = order['store_id']

            # 查找卖家
            query = "SELECT * FROM user_store WHERE store_id = %s"
            self.cursor.execute(query, (store_id,))
            seller = self.cursor.fetchone()
            seller_id = seller['user_id']

            # 计算订单总价
            query = "SELECT * FROM new_order_detail WHERE order_id = %s"
            self.cursor.execute(query, (order_id,))
            order_details = self.cursor.fetchall()
            total_price = sum(detail['count'] * detail['price'] for detail in order_details)

            # 平台将钱转给卖家
            update_query = "UPDATE user SET balance = balance + %s WHERE user_id = %s"
            self.cursor.execute(update_query, (total_price, seller_id))

            # 更新订单状态为已确认收货
            update_order_query = "UPDATE new_order SET is_received = %s WHERE order_id = %s"
            self.cursor.execute(update_order_query, (True, order_id))

            # 更新订单状态为已完成
            update_order_query = "UPDATE new_order SET order_completed = %s WHERE order_id = %s"
            self.cursor.execute(update_order_query, (True, order_id))
            self.conn.commit()

        except Exception as e:
            return 530, "{}".format(str(e))

        return 200, "ok"

    def add_funds(self, user_id, password, add_value) -> (int, str):
        try:
            user_query = "SELECT * FROM user WHERE user_id = %s"
            self.cursor.execute(user_query, (user_id,))
            user = self.cursor.fetchone()
            if user is None or user['password'] != password:
                return error.error_authorization_fail()

            update_query = "UPDATE user SET balance = balance + %s WHERE user_id = %s"
            self.cursor.execute(update_query, (add_value, user_id))
            self.conn.commit()
        except Exception as e:
            return 530, "{}".format(str(e))

        return 200, "ok"

    def query_order_status(self, user_id: str, order_id: str, password) -> (int, str, str):
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id) + ("None",)

            user_query = "SELECT * FROM user WHERE user_id = %s"
            self.cursor.execute(user_query, (user_id,))
            user = self.cursor.fetchone()
            if user['password'] != password:
                return error.error_authorization_fail() + ("None",)

            query = "SELECT * FROM new_order WHERE order_id = %s AND user_id = %s"
            self.cursor.execute(query, (order_id, user_id))
            order = self.cursor.fetchone()
            if order is None:
                return error.error_invalid_order_id(order_id) + ("None",)

            order_status = self.ORDER_STATUS[order['status']]

            return 200, "ok", order_status
        except Exception as e:
            return 530, "{}".format(str(e)) + ("None",)

    def query_buyer_all_orders(self, user_id: str, password) -> (int, str, list):
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id) + ("None",)

            user_query = "SELECT * FROM user WHERE user_id = %s"
            self.cursor.execute(user_query, (user_id,))
            user = self.cursor.fetchone()
            if user['password'] != password:
                return error.error_authorization_fail() + ("None",)

            query = "SELECT * FROM new_order WHERE user_id = %s"
            self.cursor.execute(query, (user_id,))
            orders = self.cursor.fetchall()

            return 200, "ok", orders
        except Exception as e:
            return 530, "{}".format(str(e)), None

    def cancel_order(self, user_id: str, order_id: str, password) -> (int, str):
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)

            user_query = "SELECT * FROM user WHERE user_id = %s"
            self.cursor.execute(user_query, (user_id,))
            user = self.cursor.fetchone()
            if user['password'] != password:
                return error.error_authorization_fail()

            query = "SELECT * FROM new_order WHERE order_id = %s AND user_id = %s"
            self.cursor.execute(query, (order_id, user_id))
            order = self.cursor.fetchone()
            if order is None:
                return error.error_invalid_order_id(order_id)

            if order.get('is_paid', False):
                return error.error_cannot_be_canceled(order_id)

            # 取消订单
            update_query = "UPDATE new_order SET status = %s WHERE order_id = %s"
            self.cursor.execute(update_query, ("canceled", order_id))

            # 恢复库存
            query = "SELECT * FROM new_order_detail WHERE order_id = %s"
            self.cursor.execute(query, (order_id,))
            order_details = self.cursor.fetchall()
            for detail in order_details:
                update_stock_query = "UPDATE store SET stock_level = stock_level + %s WHERE store_id = %s AND book_id = %s"
                self.cursor.execute(update_stock_query, (detail['count'], order['store_id'], detail['book_id']))

            self.conn.commit()

        except Exception as e:
            return 530, "{}".format(str(e))

        return 200, "ok"

    def auto_cancel_expired_orders(self):
        try:
            now = datetime.utcnow()
            query = "SELECT * FROM new_order WHERE is_paid = %s"
            self.cursor.execute(query, (False,))
            pending_orders = self.cursor.fetchall()

            for order in pending_orders:
                if "created_time" in order:
                    created_time = order["created_time"]
                    time_diff = abs(now - created_time)

                    if time_diff > timedelta(seconds=5):
                        order_id = order['order_id']
                        update_query = "UPDATE new_order SET status = %s WHERE order_id = %s"
                        self.cursor.execute(update_query, ("canceled", order_id))

                        # 恢复库存
                        query = "SELECT * FROM new_order_detail WHERE order_id = %s"
                        self.cursor.execute(query, (order_id,))
                        order_details = self.cursor.fetchall()
                        for detail in order_details:
                            update_stock_query = "UPDATE store SET stock_level = stock_level + %s WHERE store_id = %s AND book_id = %s"
                            self.cursor.execute(update_stock_query, (detail['count'], order['store_id'], detail['book_id']))

            self.conn.commit()
        except Exception as e:
            return 530, "not"

        return 200, "ok"