import sqlite3
import mysql.connector

# SQLite数据库路径
sqlite_db_path = 'DBLab_1_BookstoreSystem/bookstore/be/model/book.db'

# MySQL连接信息
mysql_host = 'localhost'
mysql_user = 'root'
mysql_password = '040708'
mysql_db = 'bookstore'

# 连接到SQLite数据库
def connect_sqlite():
    return sqlite3.connect(sqlite_db_path)

# 连接到MySQL数据库
def connect_mysql():
    return mysql.connector.connect(
        host=mysql_host,
        user=mysql_user,
        password=mysql_password
    )

# 创建MySQL数据库和表
def create_mysql_db_and_table(cursor):
    cursor.execute(f"DROP DATABASE IF EXISTS {mysql_db};")
    cursor.execute(f"CREATE DATABASE {mysql_db};")
    cursor.execute(f"USE {mysql_db};")
    
    cursor.execute("""
        CREATE TABLE books (
            id VARCHAR(255) PRIMARY KEY,
            title TEXT,
            author TEXT,
            publisher TEXT,
            original_title TEXT,
            translator TEXT,
            pub_year TEXT,
            pages INTEGER,
            price INTEGER,
            currency_unit TEXT,
            binding TEXT,
            isbn TEXT,
            author_intro TEXT,
            book_intro TEXT,
            content TEXT,
            tags TEXT,
            picture MEDIUMBLOB
        );
    """)

# 从SQLite读取数据并插入到MySQL中
def migrate_data():
    sqlite_conn = connect_sqlite()
    sqlite_cursor = sqlite_conn.cursor()
    
    # 获取SQLite中的数据
    sqlite_cursor.execute("SELECT * FROM book;")
    rows = sqlite_cursor.fetchall()
    
    mysql_conn = connect_mysql()
    mysql_cursor = mysql_conn.cursor()
    
    # 创建数据库和表
    create_mysql_db_and_table(mysql_cursor)
    
    # 将SQLite数据插入MySQL
    insert_query = """
        INSERT INTO books (id, title, author, publisher, original_title, translator, pub_year, 
                           pages, price, currency_unit, binding, isbn, author_intro, book_intro, 
                           content, tags, picture)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
    """
    
    for row in rows:
        mysql_cursor.execute(insert_query, row)
    
    mysql_conn.commit()
    
    # 关闭连接
    sqlite_cursor.close()
    sqlite_conn.close()
    mysql_cursor.close()
    mysql_conn.close()
    
    print("数据迁移完成！")

if __name__ == '__main__':
    migrate_data()
