import datetime
import json
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, create_engine
from sqlalchemy.orm import relationship

# 创建一个SQLite数据库引擎
engine = create_engine('sqlite:///pdf_nexus_ai.db', echo=True)  # 日志开关
# 基类
Base = declarative_base()

# 向量知识库名实体；数据库中存储


class VectorBaseInfo(Base):
    __tablename__ = 'vector_base_infos'
    id = Column(Integer, primary_key=True)
    account = Column(String(length=255))
    name = Column(String(length=255))
    detail = Column(Text, default="")
    start_time = Column(DateTime(),
                        default=datetime.datetime.now())  # 首次创建时间

    def __str__(self) -> str:
        return f"VectorBase(id={self.id}, account={self.account}, name={self.name}, start_time={self.start_time})"


# 会话字段，存储每段会话的message


class ChatSession(Base):
    __tablename__ = 'chat_sessions'
    id = Column(Integer, primary_key=True)
    account = Column(String(length=255))
    name = Column(String(length=255), default=datetime.datetime.now())
    start_time = Column(DateTime, default=datetime.datetime.now())  # 首次创建时间
    end_time = Column(DateTime)
    messages = relationship("Message")  # 第一个是类名， 第二个是表名

    def __str__(self) -> str:
        return f"VectorBase(id={self.id}, account={self.account}, name={self.name}, start_time={self.start_time})"

# message实体；即用户或系统发送的文本以及，其角色


class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True)
    account = Column(String(length=255))
    chat_session_id = Column(Integer, ForeignKey(
        'chat_sessions.id'))  # 外键是表名的外键
    role = Column(String(length=255))
    content = Column(Text)
    start_time = Column(DateTime, default=datetime.datetime.now())

    def __str__(self) -> str:
        return json.dumps({
            'role': self.role,
            'content': self.content
        })


# 建立表
Base.metadata.create_all(engine)
