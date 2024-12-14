import pymysql
from be.model import error

def test_mysql_connection():
    try:
        # 建立数据库连接
        conn = pymysql.connect(
            host='localhost',      # 数据库主机地址
            user='root',           # 数据库用户名
            password='040708',     # 数据库密码
            database='bookstore',  # 数据库名称
            port=3306             # 数据库端口号
        )
        
        print("数据库连接成功！")
        
        # 测试执行一个简单的查询
        with conn.cursor() as cursor:
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            print(f"数据库版本: {version[0]}")
            
        # 关闭连接
        conn.close()
        return True
        
    except pymysql.Error as e:
        print(f"数据库连接失败：{e}")
        return False

if __name__ == "__main__":
    test_mysql_connection() 