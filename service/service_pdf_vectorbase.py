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
from db_api.api.api_qwen import call_qwen

# LLM根据当前文本列表以及知识库描述知识库并更新


def describe_knowledge_base(vecbase_base_name: str, text_list: list):
    # 获取之前知识库描述
    vector_base_info = db.get_vector_base_info_by_name(vecbase_base_name)
    knowledge_base_detail = vector_base_info.detail
    """ 测试 """
    print(f"\nOriginal knowledge base description:\n{knowledge_base_detail}\n")
    # 构建描述提示词
    prompt = f'''
    Original description of the knowledge base:{knowledge_base_detail}
    A list of texts to add to the knowledge base:{str(text_list)}
    Constraints:
    1. Please combine these the original description with the new text list added to the knowledge base to generate a new description of the knowledge base.
    2. The knowledge base description must and only needs to describe two aspects: Knowledge base definition and Content scope.
    3. New descriptions should be no more than 100 words, just give me the new description, no need to provide other information.
    Examples:
    This is a knowledge base of relevant information about the aluminum industry. It contains multi-dimensional knowledge such as aluminum production processes, market analysis, environmental impact, policies and regulations, economic data, corporate competition landscape, and future industry trends.
    '''
    # 调用千问接口，获取新的知识库描述
    knowledge_base_detail = call_qwen([{
        "role": "user",
        "content": prompt
    }])
    """ 测试 """
    print(f"\nNew knowledge base description:\n{knowledge_base_detail}\n")
    # 更新知识库描述
    vector_base_info.detail = knowledge_base_detail
    db.update_vector_base_detail(vector_base_info)


""" 对pdf报告进行处理并放到向量库中 """


def process_pdf_vector(vector_name: str, pdf_file: str):
    # 对报告进行分割处理
    text_list = parse_pdf(pdf_file)
    # 知识库描述
    describe_knowledge_base(vector_name, text_list)
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

# 判断知识库是否存在


def vector_base_exists(name):
    return db.vector_base_exists(name)

# 创建知识库信息在数据库中


def create_vectorbase_info_db(name: str):
    vectorbase_info = VectorBaseInfo(name=name, account="test")
    if pc.create_vectorbase(name):
        db.create_vectorbase_info(vectorbase_info)
