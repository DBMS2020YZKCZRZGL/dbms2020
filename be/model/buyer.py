import sqlite3 as sqlite
import uuid
import json
import logging
from be.model import db_conn
from be.model import error
import psycopg2 as pg


class Buyer(db_conn.DBConn):
    def __init__(self):
        db_conn.DBConn.__init__(self)

    #创建新订单
    def new_order(self, user_id: str, store_id: str, id_and_count: [(str, int)]) -> (int, str, str):
        order_id = ""
        try:
            #检查id是否存在
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id) + (order_id, )
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id) + (order_id, )
            uid = "{}_{}_{}".format(user_id, store_id, str(uuid.uuid1()))

            for book_id, count in id_and_count:
                cursor = self.conn.execute(
                    "SELECT book_id, stock_level, book_info FROM store "
                    "WHERE store_id = %s AND book_id = %s;",
                    (store_id, book_id))
                row = self.conn.fetchone()
                #检查商店和书是否存在
                if row is None:
                    return error.error_non_exist_book_id(book_id) + (order_id, )

                stock_level = row['stock_level']
                book_info = row['book_info']
                book_info_json = json.loads(book_info)
                price = book_info_json.get("price")
                #检查库存是否充足
                if stock_level < count:
                    return error.error_stock_level_low(book_id) + (order_id,)
                #更改库存数量
                cursor = self.conn.execute(
                    "UPDATE store set stock_level = stock_level - %s "
                    "WHERE store_id = %s and book_id = %s and stock_level >= %s; ",
                    (count, store_id, book_id, count))
                """if cursor.rowcount == 0:
                    return error.error_stock_level_low(book_id) + (order_id, )"""

                self.conn.execute(
                        "INSERT INTO new_order_detail(order_id, book_id, count, price) "
                        "VALUES(%s, %s, %s, %s);",
                        (uid, book_id, count, price))

            self.conn.execute(
                "INSERT INTO new_order(order_id, store_id, user_id) "
                "VALUES(%s, %s, %s);",
                (uid, store_id, user_id))
            #self.conn.commit()
            order_id = uid
        except pg.Error as e:
            logging.info("528, {}".format(str(e)))
            return 528, "{}".format(str(e)), ""
        except BaseException as e:
            logging.info("530, {}".format(str(e)))
            return 530, "{}".format(str(e)), ""

        return 200, "ok", order_id

    #支付某个订单的钱款
    def payment(self, user_id: str, password: str, order_id: str) -> (int, str):
        conn = self.conn
        try:
            #检查订单是否存在
            cursor = conn.execute("SELECT order_id, user_id, store_id FROM new_order WHERE order_id = %s", (order_id,))
            row = conn.fetchone()
            if row is None:
                return error.error_invalid_order_id(order_id)

            order_id = row['order_id']
            buyer_id = row['user_id']
            store_id = row['store_id']
            #检查买家信息
            if buyer_id != user_id:
                return error.error_authorization_fail()
            #核对账户密码
            cursor = conn.execute("SELECT balance, password FROM users WHERE user_id = %s;", (buyer_id,))
            row = conn.fetchone()
            if row is None:
                return error.error_non_exist_user_id(buyer_id)
            balance = row['balance']
            if password != row['password']:
                return error.error_authorization_fail()

            #核对店铺信息
            cursor = conn.execute("SELECT store_id, user_id FROM user_store WHERE store_id = %s;", (store_id,))
            row = conn.fetchone()
            if row is None:
                return error.error_non_exist_store_id(store_id)

            seller_id = row['user_id']

            if not self.user_id_exist(seller_id):
                return error.error_non_exist_user_id(seller_id)

            conn.execute("SELECT book_id, count, price FROM new_order_detail WHERE order_id = %s;", (order_id,))
            cursor=conn.fetchall()
            total_price = 0
            bookids=[]
            counts=[]
            prices=[]
            for row in cursor:
                bookids.append(row['book_id'])
                counts.append(row['count'])
                prices.append(row['price'])
                count = row['count']
                price = row['price']
                total_price = total_price + price * count

            if balance < total_price:
                return error.error_not_sufficient_funds(order_id)
            #买家扣除相应钱款
            cursor = conn.execute("UPDATE users set balance = balance - %s"
                                  "WHERE user_id = %s AND balance >= %s",
                                  (total_price, buyer_id, total_price))
            """if cursor.rowcount == 0:
                return error.error_not_sufficient_funds(order_id)"""
            #卖家增加相应钱款
            cursor = conn.execute("UPDATE users set balance = balance + %s"
                                  "WHERE user_id = %s",
                                  (total_price, seller_id))

            """if cursor.rowcount == 0:
                return error.error_non_exist_user_id(buyer_id)"""
            #删除订单信息
            cursor = conn.execute("DELETE FROM new_order WHERE order_id = %s", (order_id, ))
            """if cursor.rowcount == 0:
                return error.error_invalid_order_id(order_id)"""

            cursor = conn.execute("DELETE FROM new_order_detail where order_id = %s", (order_id, ))
            """if cursor.rowcount == 0:
                return error.error_invalid_order_id(order_id)"""

            #增加状态信息
            cursor = conn.execute(
                "INSERT INTO paid_order(order_id,user_id,store_id,state) "
                "VALUES(%s, %s, %s, '待发货');",
                (order_id, user_id, store_id))

            for i in range(len(bookids)):
                cursor=conn.execute(
                    "INSERT INTO paid_order_detail(order_id,book_id,count,price) "
                    "VALUES(%s, %s, %s, %s);",
                    (order_id,bookids[i],counts[i],prices[i]))
            #conn.commit()

        except pg.Error as e:
            return 528, "{}".format(str(e))

        except BaseException as e:
            return 530, "{}".format(str(e))

        return 200, "ok"

    def add_funds(self, user_id, password, add_value) -> (int, str):
        try:

            cursor = self.conn.execute("SELECT password  from users where user_id=%s", (user_id,))
            row = self.conn.fetchone()
            if row is None:
                return error.error_authorization_fail()
            #核对密码信息
            if row['password'] != password:
                return error.error_authorization_fail()
            #充值
            cursor = self.conn.execute(
                "UPDATE users SET balance = balance + %s WHERE user_id = %s",
                (add_value, user_id))
            """if cursor.rowcount == 0:
                return error.error_non_exist_user_id(user_id)

            self.conn.commit()"""
        except pg.Error as e:
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))

        return 200, "ok"

    """def receive_item(self, user_id: str, order_id: str) -> (int, str):
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)

            # 检查收货人信息
            cursor = self.conn.execute("SELECT user_id,store_id,state FROM paid_order WHERE order_id = %s", (order_id,))
            row = self.conn.fetchone()
            if row is None:
                return error.error_invalid_order_id(order_id)

            buyer_id = row['user_id']
            state = row['state']
            store_id = row['store_id']
            if buyer_id != user_id:
                return error.error_authorization_fail()

            if state == '待发货':
                return error.error_receive_fail()
            elif state == '已收货':
                return error.error_repeatreceive()
            self.conn.execute("UPDATE paid_order SET state = %s "
                              "WHERE order_id = %s ", ('已收货', order_id))

            # 收货完成，该订单记录为历史订单
            cursor = self.conn.execute(
                "INSERT INTO history_order(order_id,user_id,store_id) "
                "VALUES(%s, %s, %s);",
                (order_id, user_id, store_id))

            self.conn.execute("SELECT book_id, count, price FROM paid_order_detail WHERE order_id = %s;", (order_id,))
            cursor = self.conn.fetchall()
            total_price = 0
            bookids = []
            counts = []
            prices = []
            for row in cursor:
                bookids.append(row['book_id'])
                counts.append(row['count'])
                prices.append(row['price'])

            for i in range(len(bookids)):
                cursor = self.conn.execute(
                    "INSERT INTO history_order_detail(order_id,book_id,count,price) "
                    "VALUES(%s, %s, %s, %s);",
                    (order_id, bookids[i], counts[i], prices[i]))

            # 删除订单信息
            cursor = self.conn.execute("DELETE FROM paid_order WHERE order_id = %s", (order_id,))
            cursor = self.conn.execute("DELETE FROM paid_order_detail where order_id = %s", (order_id,))

            # self.conn.commit()
        except pg.Error as e:
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"
        # 查询历史订单"""
    def receive_item(self, user_id: str, order_id: str) -> (int, str):
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            #检查收货人信息
            cursor = self.conn.execute("SELECT user_id,store_id,state FROM paid_order WHERE order_id = %s", (order_id,))
            row = self.conn.fetchone()
            if row is None:
                return error.error_invalid_order_id(order_id)
            buyer_id = row['user_id']
            state=row['state']
            store_id = row['store_id']
            if buyer_id != user_id:
                return error.error_authorization_fail()
            if state=='待发货':
                return error.error_receive_fail()
            # 收货完成，该订单记录为历史订单
            cursor = self.conn.execute(
                "INSERT INTO history_order(order_id,user_id,store_id) "
                "VALUES(%s, %s, %s);",
                (order_id, user_id, store_id))

            self.conn.execute("SELECT book_id, count, price FROM paid_order_detail WHERE order_id = %s;", (order_id,))
            cursor = self.conn.fetchall()
            total_price = 0
            bookids = []
            counts = []
            prices = []
            for row in cursor:
                bookids.append(row['book_id'])
                counts.append(row['count'])
                prices.append(row['price'])
            for i in range(len(bookids)):
                cursor = self.conn.execute(
                    "INSERT INTO history_order_detail(order_id,book_id,count,price) "
                    "VALUES(%s, %s, %s, %s);",
                    (order_id, bookids[i], counts[i], prices[i]))
            # 删除订单信息
            cursor = self.conn.execute("DELETE FROM paid_order WHERE order_id = %s", (order_id,))
            cursor = self.conn.execute("DELETE FROM paid_order_detail where order_id = %s", (order_id,))
        except pg.Error as e:
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"

    # 取消订单
    def cancel(self, user_id: str, order_id: str) -> (int, str):
        conn = self.conn
        try:
            # 订单未付款或者订单付款位发货都可以取消订单
            #如果已经付款，还会退款
            cursor = conn.execute("SELECT user_id, store_id FROM new_order WHERE order_id = %s",
                                  (order_id,))
            row_new = conn.fetchone()
            cursor = conn.execute("SELECT user_id, store_id,state FROM paid_order WHERE order_id = %s",
                                  (order_id,))
            row_paid = conn.fetchone()
            if row_new is None and row_paid is None:
                return error.error_invalid_order_id(order_id)
            elif row_new is not None:
                buyer_id = row_new['user_id']
                store_id = row_new['store_id']
                cursor = conn.execute("SELECT store_id, user_id FROM user_store WHERE store_id = %s;", (store_id,))
                row = conn.fetchone()
                seller_id = row['user_id']

                if not self.user_id_exist(seller_id):
                    return error.error_non_exist_user_id(seller_id)
                if buyer_id != user_id:
                    return error.error_authorization_fail()

                # 订单未付款，接受取消操作，该订单写入历史订单
                cursor = self.conn.execute(
                    "INSERT INTO history_order(order_id,user_id,store_id) "
                    "VALUES(%s, %s, %s);",
                    (order_id, user_id, store_id))

                self.conn.execute("SELECT book_id, count, price FROM new_order_detail WHERE order_id = %s;",
                                  (order_id,))
                cursor = self.conn.fetchall()

                bookids = []
                counts = []
                prices = []

                for row in cursor:
                    bookids.append(row['book_id'])
                    counts.append(row['count'])
                    prices.append(row['price'])


                for i in range(len(bookids)):
                    cursor = self.conn.execute(
                        "INSERT INTO history_order_detail(order_id,book_id,count,price) "
                        "VALUES(%s, %s, %s, %s);",
                        (order_id, bookids[i], counts[i], prices[i]))


                # 删除订单信息
                cursor = self.conn.execute("DELETE FROM new_order WHERE order_id = %s", (order_id,))
                cursor = self.conn.execute("DELETE FROM new_order_detail where order_id = %s", (order_id,))

                return 200, "ok"
            elif row_paid is not None:
                buyer_id = row_paid['user_id']
                store_id = row_paid['store_id']
                state = row_paid['state']
                cursor = conn.execute("SELECT store_id, user_id FROM user_store WHERE store_id = %s;", (store_id,))
                row = conn.fetchone()
                seller_id = row['user_id']

                if not self.user_id_exist(seller_id):
                    return error.error_non_exist_user_id(seller_id)
                if buyer_id != user_id:
                    return error.error_authorization_fail()
                if state == "发货中":
                    return error.error_cancel()
                # 订单未发货，接受取消操作，该订单写入历史订单，退款
                cursor = self.conn.execute(
                    "INSERT INTO history_order(order_id,user_id,store_id) "
                    "VALUES(%s, %s, %s);",
                    (order_id, user_id, store_id))

                self.conn.execute("SELECT book_id, count, price FROM paid_order_detail WHERE order_id = %s;",
                                  (order_id,))
                cursor = self.conn.fetchall()
                total_price = 0
                bookids = []
                counts = []
                prices = []

                for row in cursor:
                    bookids.append(row['book_id'])
                    counts.append(row['count'])
                    prices.append(row['price'])
                    count = row['count']
                    price = row['price']
                    total_price = total_price + price * count

                for i in range(len(bookids)):
                    cursor = self.conn.execute(
                        "INSERT INTO history_order_detail(order_id,book_id,count,price) "
                        "VALUES(%s, %s, %s, %s);",
                        (order_id, bookids[i], counts[i], prices[i]))
                # 买家增加相应钱款
                cursor = conn.execute("UPDATE users set balance = balance + %s"
                                      "WHERE user_id = %s AND balance >= %s",
                                      (total_price, buyer_id, total_price))

                # 卖家减少相应钱款
                cursor = conn.execute("UPDATE users set balance = balance - %s"
                                      "WHERE user_id = %s",
                                      (total_price, seller_id))

                # 删除订单信息
                cursor = self.conn.execute("DELETE FROM paid_order WHERE order_id = %s", (order_id,))
                cursor = self.conn.execute("DELETE FROM paid_order_detail where order_id = %s", (order_id,))

                return 200, "ok"


        except pg.Error as e:
            return 528, "{}".format(str(e))

        except BaseException as e:
            return 530, "{}".format(str(e))


    def query(self, user_id: str, order_id: str) -> (int, str, str):
        conn = self.conn
        try:
            # 检查订单进度（未付款、已付款、已交付）
            cursor = conn.execute("SELECT user_id, store_id FROM new_order WHERE order_id = %s",
                                  (order_id,))
            row_new = conn.fetchone()
            cursor = conn.execute("SELECT user_id, store_id,state FROM paid_order WHERE order_id = %s",
                                  (order_id,))
            row_paid = conn.fetchone()
            cursor = conn.execute("SELECT user_id, store_id FROM history_order WHERE order_id = %s",
                                  (order_id,))
            row_history = conn.fetchone()

            if row_new is None and row_paid is None and row_history is None:
                return error.error_invalid_order_id(order_id)
            elif row_new is not None:
                buyer_id = row_new['user_id']
                store_id = row_new['store_id']
                if buyer_id != user_id:
                    return error.error_authorization_fail()

                conn.execute("SELECT book_id, count FROM new_order_detail WHERE order_id = %s;", (order_id,))
                cursor = conn.fetchall()

                books = []
                for row in cursor:
                    dict = {}
                    dict["id"] = row['book_id']
                    dict["count"] = row['count']
                    books.append(dict)
                json_text = {}
                json_text["user_id"] = buyer_id
                json_text["store_id"] = store_id
                json_text["books"] = books
                json_text["order_state"] = "unpaid"
                return 200, "ok", str(json_text)
            elif row_paid is not None:
                buyer_id = row_paid['user_id']
                store_id = row_paid['store_id']
                state = row_paid['state']
                if buyer_id != user_id:
                    return error.error_authorization_fail()

                conn.execute("SELECT book_id, count FROM paid_order_detail WHERE order_id = %s;", (order_id,))
                cursor = conn.fetchall()

                books = []
                for row in cursor:
                    dict = {}
                    dict["id"] = row['book_id']
                    dict["count"] = row['count']
                    books.append(dict)
                json_text = {}
                json_text["user_id"] = buyer_id
                json_text["store_id"] = store_id
                json_text["books"] = books
                json_text["order_state"] = state
                return 200, "ok", str(json_text)
            elif row_history is not None:
                buyer_id = row_history['user_id']
                store_id = row_history['store_id']
                if buyer_id != user_id:
                    return error.error_authorization_fail()

                conn.execute("SELECT book_id, count FROM history_order_detail WHERE order_id = %s;", (order_id,))
                cursor = conn.fetchall()

                books = []
                for row in cursor:
                    dict = {}
                    dict["id"] = row['book_id']
                    dict["count"] = row['count']
                    books.append(dict)
                json_text = {}
                json_text["user_id"] = buyer_id
                json_text["store_id"] = store_id
                json_text["books"] = books
                json_text["order_state"] = "finished"
                return 200, "ok", str(json_text)

        except pg.Error as e:
            return 528, "{}".format(str(e))

        except BaseException as e:
            return 530, "{}".format(str(e))