import os
import concurrent.futures
import threading
import shutil

from db_api.models import VectorBaseInfo
import db_api.api.api_embedding as em
import db_api.api.api_pinecone as pc
import db_api.sqlite as db
from service.service_parse_pdf import parse_pdf
from db_api.api.api_aliyunoss import upload


""" 对pdf报告进行处理并放到向量库中 """


def process_pdf_vector(vector_name: str, pdf_file: str):
    # 对报告进行分割处理
    text_list = parse_pdf(pdf_file)
    # 上传到oss
    texts_url = upload(text_list)
    # 批量转换文本为向量
    embedding_list = em.get_batch_embeddings(texts_url)

    # 对文本与对应向量进行一个组合
    text_embedding_list = []
    for text, embedding in zip(text_list, embedding_list):
        text_embedding_list.append(
            {
                "text": text,
                "embedding": embedding
            }
        )
    # 存入向量数据库中
    pc.upsert(vector_name, text_embedding_list)
    # 打印日志
    print(f"\nIn stock: {pdf_file}\n")


# 多线程处理PDF文件


def process_pdf_vectorbase_in_threads(vector_name: str, pdf_folder: str, event: threading.Event):
    # 创建线程池
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # 将处理PDF文件的任务提交给线程池
        futures = [
            executor.submit(
                process_pdf_vector,
                vector_name,
                os.path.join(pdf_folder, pdf_name)
            )
            for pdf_name in os.listdir(pdf_folder)
        ]
    # 等待所有任务完成
    executor.shutdown(wait=True)
    # 检查并处理异常
    for future in futures:
        try:
            future.result()  # 这会抛出异常，如果任务中有任何异常
        except Exception as e:
            print(f"An error occurred while processing a PDF: {e}")
    # 通知主线程任务完成
    event.set()
    # 删除文件夹
    shutil.rmtree(pdf_folder)

# 获取所有知识库名


def get_all_vector_base():
    vector_base_info = db.get_all_vector_base_db()
    return vector_base_info

# 判断数据库是否存在


def vector_base_exists(name):
    return db.vector_base_exists(name)

# 创建向量库信息在数据库中


def create_vector_base_db(name: str):
    vectorbase_info = VectorBaseInfo(name=name, account="test")
    db.create_vectorbase_info(vectorbase_info)
