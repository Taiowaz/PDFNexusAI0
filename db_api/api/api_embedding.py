from dashscope import BatchTextEmbedding
import dashscope
import json
import tempfile
import os
import requests
import gzip
from http import HTTPStatus

""" 批量处理数据构建知识库 """

""" 创建异步处理文本转向量任务 """


def create_async_task(url: str):
    rsp = BatchTextEmbedding.async_call(
        model=BatchTextEmbedding.Models.text_embedding_async_v2,
        url=url,
        text_type="document"
    )
    if rsp.status_code == HTTPStatus.OK:
        print(rsp.output)
    else:
        print('Failed, status_code: %s, code: %s, message: %s' %
              (rsp.status_code, rsp.message))
    return rsp


""" 获取异步任务信息 """


def fetch_task_status(task):
    status = BatchTextEmbedding.fetch(task)
    if status.status_code == HTTPStatus.OK:
        print(status.output.task_status)
    else:
        print('Failed, status_code: %s, code: %s, message: %s' %
              (status.status_code, status.code, status.message))
    return status


""" 等待异步任务结束 """


def wait_task(task):
    rsp = BatchTextEmbedding.wait(task)
    if rsp.status_code == HTTPStatus.OK:
        print(rsp.output.task_status)
        return rsp.output.url
    else:
        print('Failed, status_code: %s, code: %s, message: %s' %
              (rsp.status_code, rsp.code, rsp.message))


""" 取消异步任务 """


def cancel_task(task):
    rsp = BatchTextEmbedding.cancel(task)
    if (rsp.status_code == HTTPStatus.OK):
        print(rsp.output.task_status)
    else:
        print('Filed, status_code: %s, code: %s, message: %s' %
              (rsp.status_code, rsp.code, rsp.message))
    return rsp


""" 获取向量列表 """


def get_embeddings_from_url(url: str):
    # 下载压缩包
    response = requests.get(url)
    with open(os.path.join(tempfile.gettempdir(), "embeddings_resp.txt.gz"), 'wb') as f:
        f.write(response.content)

    # 解压
    with gzip.open(os.path.join(tempfile.gettempdir(), "embeddings_resp.txt.gz"), 'rb') as f_in:
        with open(os.path.join(tempfile.gettempdir(), 'embeddings_resp.txt'), 'wb') as f_out:
            f_out.write(f_in.read())

    # 每行作为一个JSON回应，进行读取
    resp_list = []
    with open(os.path.join(tempfile.gettempdir(), 'embeddings_resp.txt'), 'r') as f:
        for line in f:
            resp_list.append(json.loads(line.strip()))

    embedding_list = []
    for resp in resp_list:
        embedding = resp["output"]["embedding"]
        embedding_list.append(embedding)

    return embedding_list


""" 单个文本转向量 """


def get_embedding(text: str) -> list:
    resp = dashscope.TextEmbedding.call(
        model=dashscope.TextEmbedding.Models.text_embedding_v2,
        input=text,
    )
    if resp.status_code == HTTPStatus.OK:
        return resp.output["embeddings"][0]["embedding"]
    else:
        print(resp)
