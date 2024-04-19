from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base
from db_api.models import VectorBaseInfo, ChatSession, Message
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy import create_engine

# 创建一个SQLite数据库引擎
engine = create_engine('sqlite:///pdf_nexus_ai.db', echo=True)  # 日志开关

# 使用 scoped_session 创建一个有范围的会话工厂
Session = scoped_session(sessionmaker(bind=engine))

""" VectorBase操作 """

# 创建向量库信息


def create_vectorbase_info(vector_base_info: VectorBaseInfo):
    session = Session()
    session.add(vector_base_info)
    session.commit()
    session.close()


# 获取所有VectorBase


def get_all_vector_base_db():
    session = Session()
    vectorbase_infos = session.query(VectorBaseInfo).all()
    vector_base_info = [{'name': base.name} for base in vectorbase_infos]
    print(vector_base_info)
    session.close()
    return vector_base_info


# 判断VectorBase是否存在


def vector_base_exists(name):
    session = Session()
    vectorbase_info = session.query(VectorBaseInfo).filter(
        VectorBaseInfo.name == name).first()
    session.close()
    return vectorbase_info is not None


""" LLM会话操作 """


def get_all_chat_session():
    session = Session()
    chat_sessions = session.query(ChatSession).all()
    session.close()
    return chat_sessions


""" 对话记录保存 """


def save_message_by_chat_session_id(message: Message):
    session = Session()
    session.add(message)
    session.commit()
    session.close()
