import jwt
import time
import logging
import sqlite3 as sqlite
from be.model import error
from be.model import db_conn
import psycopg2 as pg
import json
from psycopg2 import sql, extras
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
# encode a json string like:
#   {
#       "user_id": [user name],
#       "terminal": [terminal code],
#       "timestamp": [ts]} to a JWT
#   }


# def jwt_encode(user_id: str, terminal: str) -> str:
#     encoded = jwt.encode(
#         {"user_id": user_id, "terminal": terminal, "timestamp": time.time()},
#         key=user_id,
#         algorithm="HS256",
#     )
#     return encoded.decode("utf-8")
def jwt_encode(user_id: str, terminal: str) -> str:
    encoded = jwt.encode(
        {"user_id": user_id, "terminal": terminal, "timestamp": time.time()},
        key=user_id,
        algorithm="HS256",
    )
    return encoded


# decode a JWT to a json string like:
#   {
#       "user_id": [user name],
#       "terminal": [terminal code],
#       "timestamp": [ts]} to a JWT
#   }
def jwt_decode(encoded_token, user_id: str) -> str:
    decoded = jwt.decode(encoded_token, key=user_id, algorithms="HS256")
    return decoded
# def jwt_decode(user_id:str,terminal:str)->str:
#     encoded=jwt.encode({"user_id":user_id,"terminal":terminal,"timestamp":time.time()
#                         },
#                        key=user_id,
#                        algorithm="HS256"
#                        )
#     return encoded


class User(db_conn.DBConn):
    token_lifetime: int = 3600  # 3600 second

    def __init__(self):
        db_conn.DBConn.__init__(self)

    def __check_token(self, user_id, db_token, token) -> bool:
        try:
            if db_token != token:
                return False
            jwt_text = jwt_decode(encoded_token=token, user_id=user_id)
            ts = jwt_text["timestamp"]
            if ts is not None:
                now = time.time()
                if self.token_lifetime > now - ts >= 0:
                    return True
        except jwt.exceptions.InvalidSignatureError as e:
            print(e)
            logging.error(str(e))
            return False

    def register(self, user_id: str, password: str):
        try:
            terminal = "terminal_{}".format(str(time.time()))
            token = jwt_encode(user_id, terminal)
            self.conn.execute(
                "INSERT into users(user_id, password, balance, token, terminal) "
                "VALUES (%s, %s, %s, %s, %s);",
                (user_id, password, 0, token, terminal), )
            #self.conn.commit()
        except pg.Error:
            return error.error_exist_user_id(user_id)
        return 200, "ok"

    def check_token(self, user_id: str, token: str) -> (int, str):
        cursor = self.conn.execute("SELECT token from users where user_id=%s", (user_id,))
        row = self.conn.fetchone()
        if row is None:
            return error.error_authorization_fail()
        db_token = row['token']
        if not self.__check_token(user_id, db_token, token):
            return error.error_authorization_fail()
        return 200, "ok"

    def check_password(self, user_id: str, password: str) -> (int, str):
        self.conn.execute("SELECT password from users where user_id=%s", (user_id,))
        row = self.conn.fetchone()
        if row is None:
            return error.error_authorization_fail()

        if password != row['password']:
            return error.error_authorization_fail()

        return 200, "ok"

    def login(self, user_id: str, password: str, terminal: str) -> (int, str, str):
        token = ""
        try:
            code, message = self.check_password(user_id, password)
            if code != 200:
                return code, message, ""

            token = jwt_encode(user_id, terminal)
            cursor = self.conn.execute(
                "UPDATE users set token= %s , terminal = %s where user_id = %s",
                (token, terminal, user_id), )
            """if cursor.rowcount == 0:
                return error.error_authorization_fail() + ("", )"""
           # self.conn.commit()
        except pg.Error as e:
            print(e)
            return 528, "{}".format(str(e)), ""
        except BaseException as e:
            print(e)
            return 530, "{}".format(str(e)), ""
        return 200, "ok", token

    def logout(self, user_id: str, token: str) -> bool:
        try:
            code, message = self.check_token(user_id, token)
            if code != 200:
                return code, message

            terminal = "terminal_{}".format(str(time.time()))
            dummy_token = jwt_encode(user_id, terminal)

            cursor = self.conn.execute(
                "UPDATE users SET token = %s, terminal = %s WHERE user_id=%s",
                (dummy_token, terminal, user_id), )
            """if cursor.rowcount == 0:
                return error.error_authorization_fail()

            self.conn.commit()"""
        except pg.Error as e:
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"

    def unregister(self, user_id: str, password: str) -> (int, str):
        try:
            code, message = self.check_password(user_id, password)
            if code != 200:
                return code, message

            cursor = self.conn.execute("DELETE from users where user_id=%s", (user_id,))
            """if self.conn.rowcount == 1:
                self.conn.commit()
            else:
                return error.error_authorization_fail()"""
        except pg.Error as e:
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"

    def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        try:
            code, message = self.check_password(user_id, old_password)
            if code != 200:
                return code, message

            terminal = "terminal_{}".format(str(time.time()))
            token = jwt_encode(user_id, terminal)
            cursor = self.conn.execute(
                "UPDATE users set password = %s, token= %s , terminal = %s where user_id = %s",
                (new_password, token, terminal, user_id), )
            """if cursor.rowcount == 0:
                return error.error_authorization_fail()

            self.conn.commit()"""
        except pg.Error as e:
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"

    # def search_by_store_id(self,target_store_id):
    #   self.conn.execute("""
    #   select * from store
    #   """)
    #   ret=[]
    #   ans = self.conn.fetchall()
    #   for entry in ans:
    #     store_id = entry['store_id']
    #     if store_id==target_store_id:
    #       ret.append(dict(entry))
    #   return 200,ret
    #
    # def search_by_tags(self,target_tags:list,target_store_id=None):#tags列表，可有多个。搜索包含其中所有tags的内容。
    #     by_store=False
    #     if target_store_id!=None:
    #       by_store=True
    #     if target_store_id==None:
    #         self.conn.execute("""
    #       select * from store
    #       """)
    #     else:
    #         self.conn.execute("""
    #             select * from store where store_id=%s
    #             """,(target_store_id,))
    #     ans = self.conn.fetchall()
    #     ret=[]
    #     for entry in ans:
    #       book_info = entry['book_info']
    #       book_info = json.loads(book_info)
    #       tags = book_info['tags']
    #       if all(item in tags for item in target_tags):
    #         ret.append(dict(entry))
    #     return 200,ret
    #

    def search_by_arguments(self,target_store_id:list=None,target_id:list=None,target_title:list=None,target_tags:list=None,
                            target_author:list=None,target_publisher:list=None,target_original_title:list=None,target_translator:list=None,
                            target_pub_year:list=None,target_pages:list=None,target_price:list=None,target_binding:list=None,
                            target_isbn:list=None,target_author_intro:list=None,target_book_intro:list=None,target_content:list=None,
                            target_stock_level:int=None
                            ):
        if target_store_id == None or target_store_id==[]:#全站搜索
          self.conn.execute("""
            select * from store
            """)
        else:#指定店铺
          if len(target_store_id)==1:
            self.conn.execute("""
                    select * from store where store_id=%s
                    """, (target_store_id[0],))
          else:
            cond='store_id='+'\''+target_store_id[0]+'\''
            for x in target_store_id[1:]:
              cond+=' or store_id='+'\''+x+'\''
            print(cond)
            self.conn.execute("""
                    select * from store where {}
                    """.format(cond,))
        ans = self.conn.fetchall()
        ret = []
        for entry in ans:
            flag = 1
            store_id = entry['store_id']
            stock_level = entry['stock_level']
            book_info = entry['book_info']
            book_info = json.loads(book_info)
            tags = book_info['tags']
            pictures = book_info['pictures']
            id = book_info['id']
            title = book_info['title']
            author = book_info['author']
            publisher = book_info['publisher']
            original_title = book_info['original_title']
            translator = book_info['translator']
            pub_year = book_info['pub_year']
            pages = book_info['pages']
            price = book_info['price']
            binding = book_info['binding']
            isbn = book_info['isbn']
            author_intro = book_info['author_intro']
            book_intro = book_info['book_intro']
            content = book_info['content']
            if target_id!=None and target_id!=[] and not any(item in id for item in target_id):#id任意满足

              continue
            if target_tags != None and target_tags !=[] and not all(item in tags for item in target_tags):#tag要全部满足

              continue
            if target_title!=None and target_title!=[] and not any(item in title for item in target_title):

              continue
            if target_author!=None and target_author!=[] and not any(i in author for i in target_author):

              continue
            if target_publisher!=None and target_publisher!=[] and not any(i in publisher for i in target_publisher):

              continue
            if target_original_title!=None and target_original_title!=[] and not any(i in original_title for i in target_original_title):

              continue
            if target_translator!=None and target_translator!=[] and not any(i in translator for i in target_translator):

              continue
            if target_pub_year!=None and target_pub_year!=[] and not any(i in pub_year for i in target_pub_year):

              continue
            if target_pages!=None and target_pages!=[] and not any(i in pages for i in target_pages):

              continue
            if target_price!=None and target_price!=[] and not any(i in price for i in target_price):

              continue
            if target_binding!=None and target_binding!=[] and not any(i in binding for i in target_binding):

              continue
            if target_isbn!=None and target_isbn!=[] and not any(i in isbn for i in target_isbn):

              continue
            if target_author_intro!=None and target_author_intro!=[] and not any(i in author_intro for i in target_author_intro):

              continue
            if target_book_intro!=None and target_book_intro!=[] and not any(i in book_intro for i in target_book_intro):

              continue
            if target_content!=None and target_content!=[] and not any(i in content for i in target_content):

              continue
            if target_stock_level!=None and target_stock_level > stock_level:
              continue
            if flag==1:
              ret.append(dict(entry))

        return 200, ret