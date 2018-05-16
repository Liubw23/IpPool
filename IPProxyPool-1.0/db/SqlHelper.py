# coding:utf-8
import datetime
from sqlalchemy import create_engine
from sqlalchemy import Column
from sqlalchemy import Integer, VARCHAR, String, DateTime, Numeric  # 数据类型
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import DB_CONFIG

from db.ISqlHelper import ISqlHelper

'''
sql操作的基类
包括ip，端口，types类型(0高匿名，1透明)，protocol(0 http,1 https http),country(国家),area(省市),updatetime(更新时间)
 speed(连接速度)
'''

BaseModel = declarative_base()  # 生成模型类


# 创建模型类
class Proxy(BaseModel):
    __tablename__ = 'proxys'
    id = Column(Integer, primary_key=True, autoincrement=True)  # 主键，自增
    ip = Column(VARCHAR(16), nullable=False)
    port = Column(Integer, nullable=False)
    types = Column(Integer, nullable=False)
    protocol = Column(Integer, nullable=False, default=0)
    country = Column(VARCHAR(100), nullable=False)
    area = Column(VARCHAR(100), nullable=False)
    updatetime = Column(DateTime(), default=datetime.datetime.utcnow)
    speed = Column(Numeric(5, 2), nullable=False)
    score = Column(Integer, nullable=False, default=0)


class SqlHelper(ISqlHelper):
    params = {'ip': Proxy.ip, 'port': Proxy.port, 'types': Proxy.types, 'protocol': Proxy.protocol,
              'country': Proxy.country, 'area': Proxy.area, 'score': Proxy.score}

    def __init__(self):

        # sqlalchemy.create_engine() 创建一个引擎
        if 'sqlite' in DB_CONFIG['DB_CONNECT_STRING']:
            connect_args = {'check_same_thread': False}
            self.engine = create_engine(DB_CONFIG['DB_CONNECT_STRING'], echo=False, connect_args=connect_args)
        else:
            self.engine = create_engine(DB_CONFIG['DB_CONNECT_STRING'], echo=False)  # echo=True 会打印所有的sql语句

        DB_Session = sessionmaker(bind=self.engine)  # sqlalchemy.sessionmaker()  创建一个session类，关联引擎

        self.session = DB_Session()  # 生成一个Session对象

    def init_db(self):
        BaseModel.metadata.create_all(self.engine)

    def drop_db(self):
        BaseModel.metadata.drop_all(self.engine)

    def insert(self, value):
        proxy = Proxy(ip=value['ip'], 
                      port=value['port'], 
                      types=value['types'], 
                      protocol=value['protocol'],
                      country=value['country'],
                      area=value['area'], 
                      speed=value['speed'])
        self.session.add(proxy)
        self.session.commit()

    def delete(self, conditions=None):
        if conditions:
            conditon_list = []
            for key in list(conditions.keys()):
                if self.params.get(key, None):
                    conditon_list.append(self.params.get(key) == conditions.get(key))
            conditions = conditon_list
            query = self.session.query(Proxy)
            for condition in conditions:
                query = query.filter(condition)
            delete_num = query.delete()
            self.session.commit()
        else:
            delete_num = 0
        return 'deleteNum', delete_num

    def update(self, conditions=None, value=None):
        """
        conditions的格式是个字典。类似self.params
        :param conditions:
        :param value: 也是个字典：{'ip':192.168.0.1}
        :return:
        """
        if conditions and value:
            conditon_list = []
            for key in list(conditions.keys()):
                if self.params.get(key, None):
                    conditon_list.append(self.params.get(key) == conditions.get(key))
            conditions = conditon_list
            query = self.session.query(Proxy)
            for condition in conditions:
                query = query.filter(condition)
            updatevalue = {}
            for key in list(value.keys()):
                if self.params.get(key, None):
                    updatevalue[self.params.get(key, None)] = value.get(key)
            updateNum = query.update(updatevalue)
            self.session.commit()
        else:
            updateNum = 0
        return {'updateNum': updateNum}

    def select(self, count=None, conditions=None):
        """
        conditions的格式是个字典。类似self.params
        :param count:
        :param conditions:
        :return:
        """
        if conditions:
            conditon_list = []
            for key in list(conditions.keys()):
                if self.params.get(key, None):
                    conditon_list.append(self.params.get(key) == conditions.get(key))
            conditions = conditon_list
        else:
            conditions = []

        query = self.session.query(Proxy.ip, Proxy.port, Proxy.score)
        if len(conditions) > 0 and count:
            for condition in conditions:
                query = query.filter(condition)
            return query.order_by(Proxy.score.desc(), Proxy.speed).limit(count).all()
        elif count:
            return query.order_by(Proxy.score.desc(), Proxy.speed).limit(count).all()
        elif len(conditions) > 0:
            for condition in conditions:
                query = query.filter(condition)
            return query.order_by(Proxy.score.desc(), Proxy.speed).all()
        else:
            return query.order_by(Proxy.score.desc(), Proxy.speed).all()

    def close(self):
        self.session.close()  # 关闭会话


if __name__ == '__main__':
    sqlhelper = SqlHelper()
    sqlhelper.init_db()
    proxy = {'ip': '192.168.1.1', 'port': 80, 'types': 0, 'protocol': 0, 'country': '中国', 'area': '广州', 'speed': 11}
    sqlhelper.insert(proxy)
