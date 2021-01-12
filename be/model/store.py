import logging
import os
import sqlite3 as sqlite
import psycopg2 as pg
from psycopg2 import sql, extras
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from flask import Flask, render_template, request, flash, url_for, json, jsonify, redirect
import pytest, coverage
import time
import random


class Store:
    # def __init__(self, db_path):
    #     self.database = os.path.join(db_path, "be.db")
    #     self.init_tables()
    db_cur=0
    def __init__(self):
        db_conn = pg.connect('dbname=postgres user=postgres password=1')
        db_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        db_cur = db_conn.cursor(cursor_factory=pg.extras.RealDictCursor)
        db_cur.execute("SELECT * FROM pg_catalog.pg_database WHERE datname = 'bookstore'")
        exists = db_cur.fetchone()
        # print(exists)
        if not exists:
            db_cur.execute('CREATE DATABASE bookstore')
        db_cur.close()
        db_conn.close()
        db_conn = pg.connect('dbname=bookstore user=postgres password=1')
        db_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        db_cur = db_conn.cursor(cursor_factory=pg.extras.RealDictCursor)
        cur = db_cur
        db_cur.execute("""SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'""")
        tablenames_ = cur.fetchall()
        tablenames=[]
        for x in tablenames_:
            tablenames.append(x['table_name'])
        self.db_cur=db_cur
        if 'users' not in tablenames:
            db_cur.execute('''
                CREATE TABLE users(
                user_id TEXT PRIMARY KEY,
                 password TEXT NOT NULL, 
                balance INTEGER NOT NULL,
                 token TEXT,
                  terminal TEXT)'''
            )
            db_cur.execute("""
            create index user_id_idx on users(user_id)
            """)

        if 'user_store' not in tablenames:
            cur.execute(
                "CREATE TABLE  user_store("
                "user_id TEXT, store_id text, PRIMARY KEY(user_id, store_id));"
            )
            cur.execute("""
            create index if not exists user_id_idx on user_store(user_id)
            """)
        if 'store' not in tablenames:
            cur.execute(
                "CREATE TABLE store( "
                "store_id TEXT, book_id TEXT, book_info TEXT, stock_level INTEGER,"
                " PRIMARY KEY(store_id, book_id))"
            )
            cur.execute("""
            create index if not exists store_idx on store(store_id,book_id)
            """)
        if 'new_order' not in tablenames:
            cur.execute(
                "CREATE TABLE new_order( "
                "order_id TEXT PRIMARY KEY, user_id TEXT, store_id TEXT)"
            )
            cur.execute("""
            create index if not exists new_order_idx on new_order(order_id,user_id)
            """)
        if 'new_order_detail' not in tablenames:
            cur.execute(
                "CREATE TABLE new_order_detail( "
                "order_id TEXT, book_id TEXT, count INTEGER, price INTEGER,  "
                "PRIMARY KEY(order_id, book_id))"
            )
            cur.execute("""
            create index if not exists new_order_detail_idx on new_order_detail(order_id,book_id)
            """)
        if 'paid_order' not in tablenames:
            cur.execute(
                """
                create table paid_order(
                order_id text PRIMARY KEY,user_id text,store_id text,state text
                )
                """
            )
            cur.execute("""
            create index if not exists paid_order_idx on paid_order(order_id,user_id)
            """)
        if 'paid_order_detail' not in tablenames:
            cur.execute(
                """
                create table paid_order_detail(
                order_id text, book_id TEXT, count INTEGER, price INTEGER,
                PRIMARY KEY(order_id, book_id)
                )
                """
            )
            cur.execute("""
                        create index if not exists paid_order_detail_idx on paid_order_detail(order_id,book_id)
                        """)
        if 'history_order' not in tablenames:
            cur.execute(
                """
                create table history_order(
                order_id text PRIMARY KEY,user_id text,store_id text
                )
                """
            )
            cur.execute("""
            create index if not exists history_order_idx on history_order(order_id,user_id)
            """)
        if 'history_order_detail' not in tablenames:
            cur.execute(
                """
                create table history_order_detail(
                order_id text, book_id TEXT, count INTEGER, price INTEGER,
                PRIMARY KEY(order_id, book_id)
                )
                """
            )
            cur.execute("""
            create index if not exists history_order_detail_idx on history_order_detail(order_id,book_id)
            """)
    def get_db_conn(self):
        return self.db_cur


# database_instance: Store = None


def init_database():
    print('init')
    global database_instance
    database_instance = Store()
    #database_instance.init_tables()

#init_database()
def get_db_conn():
    global database_instance
    return database_instance.db_cur
