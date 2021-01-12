import pytest

from fe.access.new_seller import register_new_seller
from fe.access import book
from fe.access import auth
from urllib.parse import urljoin
from fe import conf
import uuid


class TestSearchByArgs:
    @pytest.fixture(autouse=True)
    def pre_run_initialization(self):
        # do before test
        self.seller_id1 = "test_add_books_seller_id_{}".format(str(uuid.uuid1()))
        self.store_id1 = "test_add_books_store_id_{}".format(str(uuid.uuid1()))
        self.password = self.seller_id1
        self.seller1 = register_new_seller(self.seller_id1, self.password)

        code = self.seller1.create_store(self.store_id1)
        assert code == 200
        book_db = book.BookDB()
        self.books1 = book_db.get_book_info(0, 10)

        self.seller_id2 = "test_add_books_seller_id_{}".format(str(uuid.uuid1()))
        self.store_id2 = "test_add_books_store_id_{}".format(str(uuid.uuid1()))
        self.password = self.seller_id2
        self.seller2 = register_new_seller(self.seller_id2, self.password)

        code = self.seller2.create_store(self.store_id2)
        assert code == 200
        book_db = book.BookDB()
        self.books2 = book_db.get_book_info(10,5 )

        self.seller_id3 = "test_add_books_seller_id_{}".format(str(uuid.uuid1()))
        self.store_id3 = "test_add_books_store_id_{}".format(str(uuid.uuid1()))
        self.password = self.seller_id3
        self.seller3 = register_new_seller(self.seller_id3, self.password)

        code = self.seller3.create_store(self.store_id3)
        assert code == 200
        book_db = book.BookDB()
        self.books3 = book_db.get_book_info(99, 7)
        for b in self.books1:
            code = self.seller1.add_book(self.store_id1,0,b)
            assert code == 200
        for b in self.books2:
            code = self.seller2.add_book(self.store_id2,0,b)
            assert code == 200
        for b in self.books3:
            code = self.seller3.add_book(self.store_id3,0,b)
            assert code == 200
        yield
        # do after test

    def test_ok1(self):
        store_id=None
        id=None
        title=None
        author=None
        publisher=None
        original_title=None
        translator=None
        pub_year=None
        pages=None
        price=None
        binding=None
        isbn=None
        author_intro=None
        book_intro=None
        content=None
        tags=None
        stock_level=None

        info1=[]

        info1.append(store_id)
        info1.append(id)
        info1.append(title)
        info1.append(author)
        info1.append(publisher)
        info1.append(original_title)
        info1.append(translator)
        info1.append(pub_year)
        info1.append(pages)
        info1.append(price)
        info1.append(binding)
        info1.append(isbn)
        info1.append(author_intro)
        info1.append(book_intro)
        info1.append(content)
        info1.append(tags)
        info1.append(stock_level)

        a=auth.Auth(conf.URL)
        code=a.search(info1)
        assert code == 200

    def test_ok2(self):
        xx='cfwenvjhcwu'
        store_id = [self.store_id1,self.store_id2]
        id = [xx]
        title = [xx]
        author = [xx]
        publisher = [xx]
        original_title = [xx]
        translator = [xx]
        pub_year = [xx]
        pages = [xx]
        price = [xx]
        binding = [xx]
        isbn = [xx]
        author_intro = [xx]
        book_intro = [xx]
        content = [xx]
        tags = [xx]
        stock_level = -1

        info1 = []

        info1.append(store_id)
        info1.append(id)
        info1.append(title)
        info1.append(author)
        info1.append(publisher)
        info1.append(original_title)
        info1.append(translator)
        info1.append(pub_year)
        info1.append(pages)
        info1.append(price)
        info1.append(binding)
        info1.append(isbn)
        info1.append(author_intro)
        info1.append(book_intro)
        info1.append(content)
        info1.append(tags)
        info1.append(stock_level)

        a = auth.Auth(conf.URL)
        code = a.search(info1)
        assert code == 200
