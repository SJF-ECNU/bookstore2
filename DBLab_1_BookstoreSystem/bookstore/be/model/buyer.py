import pymysql
import uuid
import json
import logging
from be.model import db_conn
from be.model import error
from datetime import datetime, timedelta

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
        # 连接MySQL数据库
        self.connection = pymysql.connect(
            host='localhost',
            user='root',       # 替换为您的MySQL数据库用户名
            password='040708',  # 替换为您的数据库密码
            database='bookstore',      # 使用bookstore数据库
            cursorclass=pymysql.cursors.DictCursor
        )
        self.cursor = self.connection.cursor()

    def user_id_exist(self, user_id):
        # 检查 user_id 是否存在
        self.cursor.execute("SELECT * FROM user WHERE user_id = %s", (user_id,))
        user = self.cursor.fetchone()
        return user is not None

    def store_id_exist(self, store_id):
        # 检查 store_id 是否存在
        self.cursor.execute("SELECT * FROM store WHERE store_id = %s", (store_id,))
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
                self.cursor.execute("SELECT * FROM store WHERE store_id = %s AND book_id = %s", (store_id, book_id))
                store_item = self.cursor.fetchone()
                if store_item is None:
                    return error.error_non_exist_book_id(book_id) + (order_id,)
                
                stock_level = store_item['stock_level']
                book_info = json.loads(store_item['book_info'])
                price = book_info.get("price")

                if stock_level < count:
                    return error.error_stock_level_low(book_id) + (order_id,)
                
                # 更新库存
                self.cursor.execute(
                    "UPDATE store SET stock_level = stock_level - %s WHERE store_id = %s AND book_id = %s AND stock_level >= %s", 
                    (count, store_id, book_id, count)
                )
                self.connection.commit()
                
                # 插入订单详情
                self.cursor.execute(
                    "INSERT INTO new_order_detail (order_id, book_id, count, price) VALUES (%s, %s, %s, %s)",
                    (uid, book_id, count, price)
                )
                self.connection.commit()
            
            # 插入订单
            self.cursor.execute(
                "INSERT INTO new_order (order_id, store_id, user_id, is_paid, is_shipped, is_received, order_completed, status, created_time) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (uid, store_id, user_id, False, False, False, False, 'pending', datetime.utcnow())
            )
            self.connection.commit()
            order_id = uid
        except Exception as e:
            logging.error(f"530, {str(e)}")
            return 530, "{}".format(str(e)), ""

        return 200, "ok", order_id

    def pay_to_platform(self, user_id: str, password: str, order_id: str) -> (int, str): 
        try:
            # 查找订单
            self.cursor.execute("SELECT * FROM new_order WHERE order_id = %s", (order_id,))
            order = self.cursor.fetchone()
            if order is None:
                return error.error_invalid_order_id(order_id)

            buyer_id = order['user_id']

            # 检查用户身份
            if buyer_id != user_id:
                return error.error_authorization_fail()

            self.cursor.execute("SELECT * FROM user WHERE user_id = %s", (buyer_id,))
            user = self.cursor.fetchone()
            if user is None or user['password'] != password:
                return error.error_authorization_fail()
                
            # 检查是否已经付款
            if order.get('is_paid', False):
                return error.error_order_is_paid(order_id)

            # 计算订单总价
            self.cursor.execute("SELECT * FROM new_order_detail WHERE order_id = %s", (order_id,))
            order_details = self.cursor.fetchall()
            total_price = sum(detail['count'] * detail['price'] for detail in order_details)

            if user['balance'] < total_price:
                return error.error_not_sufficient_funds(order_id)

            # 扣除买家的余额，平台收款
            self.cursor.execute(
                "UPDATE user SET balance = balance - %s WHERE user_id = %s AND balance >= %s",
                (total_price, buyer_id, total_price)
            )
            self.connection.commit()

            # 更新订单状态为已付款
            self.cursor.execute(
                "UPDATE new_order SET is_paid = %s WHERE order_id = %s",
                (True, order_id)
            )
            self.connection.commit()

        except Exception as e:
            return 530, "{}".format(str(e))

        return 200, "ok"

    def confirm_receipt_and_pay_to_seller(self, user_id: str, password: str, order_id: str) -> (int, str): 
        try:
            # 查找订单
            self.cursor.execute("SELECT * FROM new_order WHERE order_id = %s", (order_id,))
            order = self.cursor.fetchone()

            buyer_id = order['user_id']

            # 检查用户身份
            if buyer_id != user_id:
                return error.error_authorization_fail()
            self.cursor.execute("SELECT * FROM user WHERE user_id = %s", (buyer_id,))
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

            self.cursor.execute("SELECT * FROM user_store WHERE store_id = %s", (store_id,))
            seller = self.cursor.fetchone()
            seller_id = seller['user_id']

            # 计算订单总价
            self.cursor.execute("SELECT * FROM new_order_detail WHERE order_id = %s", (order_id,))
            order_details = self.cursor.fetchall()
            total_price = sum(detail['count'] * detail['price'] for detail in order_details)

            # 平台将钱转给卖家
            self.cursor.execute(
                "UPDATE user SET balance = balance + %s WHERE user_id = %s",
                (total_price, seller_id)
            )
            self.connection.commit()

            # 更新订单状态为已确认收货
            self.cursor.execute(
                "UPDATE new_order SET is_received = %s WHERE order_id = %s",
                (True, order_id)
            )
            self.connection.commit()

            # 更新订单状态为已完成
            self.cursor.execute(
                "UPDATE new_order SET order_completed = %s WHERE order_id = %s",
                (True, order_id)
            )
            self.connection.commit()

        except Exception as e:
            return 530, "{}".format(str(e))

        return 200, "ok"

    # 其他方法同理，可继续修改SQL查询来适配MySQL
    def close(self):
        # 关闭数据库连接
        self.cursor.close()
        self.connection.close()
