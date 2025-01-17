import time
import pytest
from fe.access import auth
from fe import conf
from be.model.store import Store  # 假设 Store 中管理 MySQL 连接

class TestRegister:
    @pytest.fixture(autouse=True)
    def pre_run_initialization(self):
        # 每次测试运行前生成唯一的 user_id 和 password
        self.user_id = "test_register_user_{}".format(time.time())
        self.password = "test_register_password_{}".format(time.time())
        self.auth = auth.Auth(conf.URL)
        
        # 清空数据库中的用户数据
        store = Store()
        cursor = store.conn.cursor()  # 获取 MySQL 游标
        cursor.execute("DELETE FROM user")  # 清空 user 表
        store.conn.commit()  # 提交事务
        
        yield

    def test_register_ok(self):
        code = self.auth.register(self.user_id, self.password)
        assert code == 200

    def test_unregister_ok(self):
        code = self.auth.register(self.user_id, self.password)
        assert code == 200

        code = self.auth.unregister(self.user_id, self.password)
        assert code == 200

    def test_unregister_error_authorization(self):
        code = self.auth.register(self.user_id, self.password)
        assert code == 200

        code = self.auth.unregister(self.user_id + "_x", self.password)
        assert code != 200

        code = self.auth.unregister(self.user_id, self.password + "_x")
        assert code != 200

    def test_register_error_exist_user_id(self):
        code = self.auth.register(self.user_id, self.password)
        assert code == 200

        code = self.auth.register(self.user_id, self.password)
        assert code != 200