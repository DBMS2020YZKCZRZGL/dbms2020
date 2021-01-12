import sqlite3 as sqlite
from be.model import error
from be.model import db_conn
import psycopg2 as pg


class Seller(db_conn.DBConn):

    def __init__(self):
        db_conn.DBConn.__init__(self)

    #添加书的信息。从user_store\store\users中查询id是否存在。书的信息不能已经存在。
    #向store中插入书的信息，包括卖家id、书id、书信息（结构体）、库存数量。
    def add_book(self, user_id: str, store_id: str, book_id: str, book_json_str: str, stock_level: int):
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id)
            if self.book_id_exist(store_id, book_id):
                return error.error_exist_book_id(book_id)

            self.conn.execute("INSERT into store(store_id, book_id, book_info, stock_level)"
                              "VALUES (%s, %s, %s, %s)", (store_id, book_id, book_json_str, stock_level))
            #self.conn.commit()
        except pg.Error as e:
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"

    #增加书的库存水平。用户、店铺、书必须存在。将指定店铺中指定书籍的库存容量增加add_stock_level个。
    def add_stock_level(self, user_id: str, store_id: str, book_id: str, add_stock_level: int):
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id)
            if not self.book_id_exist(store_id, book_id):
                return error.error_non_exist_book_id(book_id)

            self.conn.execute("UPDATE store SET stock_level = stock_level + %s "
                              "WHERE store_id = %s AND book_id = %s", (add_stock_level, store_id, book_id))
            #self.conn.commit()
        except pg.Error as e:
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"

    #创建店铺。用户id不能不存在，店铺id不能已经存在。向user_store中插入（店铺，用户）对
    def create_store(self, user_id: str, store_id: str) -> (int, str):
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            if self.store_id_exist(store_id):
                return error.error_exist_store_id(store_id)
            self.conn.execute("INSERT into user_store(store_id, user_id)"
                              "VALUES (%s, %s)", (store_id, user_id))
            #self.conn.commit()
        except pg.Error as e:
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"

    """def send_item(self, user_id: str, order_id: str) -> (int, str):
        try:

            #检查发货人信息
            cursor = self.conn.execute("SELECT store_id,state FROM paid_order WHERE order_id = %s", (order_id,))
            row = self.conn.fetchone()
            if row is None:
                return error.error_invalid_order_id(order_id)
            store_id = row['store_id']
            state=row['state']
            cursor = self.conn.execute("SELECT user_id FROM user_store WHERE store_id = %s", (store_id,))
            row = self.conn.fetchone()
            seller_id = row['user_id']
            if seller_id != user_id:
                return error.error_authorization_fail()
            if state=='已收货':
                return error.error_send_fail()
            elif state=='发货中':
                return error.error_repeatsend()
            self.conn.execute("UPDATE paid_order SET state = %s "
                              "WHERE order_id = %s ", ('发货中',order_id))

            #self.conn.commit()
        except pg.Error as e:
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"""""
    def send_item(self, user_id: str, order_id: str) -> (int, str):
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            #检查发货人信息
            cursor = self.conn.execute("SELECT store_id,state FROM paid_order WHERE order_id = %s", (order_id,))
            row = self.conn.fetchone()
            if row is None:
                return error.error_invalid_order_id(order_id)
            store_id = row['store_id']
            state=row['state']
            cursor = self.conn.execute("SELECT user_id FROM user_store WHERE store_id = %s", (store_id,))
            row = self.conn.fetchone()
            seller_id = row['user_id']
            if seller_id != user_id:
                return error.error_authorization_fail()
            if state=='发货中':
                return error.error_repeatsend()
            self.conn.execute("UPDATE paid_order SET state = %s "
                              "WHERE order_id = %s ", ('发货中',order_id))

            #self.conn.commit()
        except pg.Error as e:
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"





