import os
import random
import base64
import simplejson as json
import mysql.connector
from mysql.connector import Error

class Book:
    id: str
    title: str
    author: str
    publisher: str
    original_title: str
    translator: str
    pub_year: str
    pages: int
    price: int
    currency_unit: str
    binding: str
    isbn: str
    author_intro: str
    book_intro: str
    content: str
    tags: list
    pictures: list

    def __init__(self):
        self.tags = []
        self.pictures = []


class BookDB:
    def __init__(self, large: bool = False):
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
            print(f"Error while connecting to MySQL: {e}")

    def get_book_count(self):
        query = "SELECT COUNT(*) as count FROM books"
        self.cursor.execute(query)
        result = self.cursor.fetchone()
        return result["count"] if result else 0

    import json

    def get_book_info(self, start, size) -> list[Book]:
        books = []
        query = "SELECT * FROM books LIMIT %s OFFSET %s"
        self.cursor.execute(query, (size, start))
        rows = self.cursor.fetchall()

        for row in rows:
            book = Book()
            book.id = str(row.get('id'))  # MySQL的自增ID字段
            book.title = row.get('title')
            book.author = row.get('author')
            book.publisher = row.get('publisher')
            book.original_title = row.get('original_title')
            book.translator = row.get('translator')
            book.pub_year = row.get('pub_year')
            book.pages = row.get('pages')
            book.price = row.get('price')
            book.currency_unit = row.get('currency_unit')
            book.binding = row.get('binding')
            book.isbn = row.get('isbn')
            book.author_intro = row.get('author_intro')
            book.book_intro = row.get('book_intro')
            book.content = row.get('content')
            
            # 处理 tags 字段
            tags = row.get('tags', "")
            try:
                # 尝试解析 JSON
                book.tags = json.loads(tags)
            except json.JSONDecodeError:
                # 如果解析失败，将 tags 拆分为列表
                book.tags = [tag.strip() for tag in tags.split("\n") if tag.strip()]
            
            # 处理二进制图片数据
            picture_binary = row.get('picture')
            if picture_binary:
                picture_base64 = base64.b64encode(picture_binary).decode('utf-8')
                book.pictures.append(picture_base64)

            books.append(book)
        return books