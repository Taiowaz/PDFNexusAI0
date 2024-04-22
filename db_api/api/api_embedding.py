from cgitb import text
from dashscope import BatchTextEmbedding
import dashscope
import json
import tempfile
import os
import requests
import gzip
from http import HTTPStatus

""" 批量处理文本转向量 """


def get_batch_embeddings(texts_url: str) -> list:
    rsp = BatchTextEmbedding.call(
        model=BatchTextEmbedding.Models.text_embedding_async_v1,
        url=texts_url,
        text_type="document"
    )
    if rsp.status_code == HTTPStatus.OK:
        # 获取向量列表
        embedding_list = get_embeddings_from_url(rsp.output.url)
        return embedding_list
    else:
        print(rsp)
        return []


""" 获取向量列表 """


def get_embeddings_from_url(url: str) -> list:
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


def get_single_embedding(text: str) -> list:
    resp = dashscope.TextEmbedding.call(
        model=dashscope.TextEmbedding.Models.text_embedding_v2,
        input=text,
    )
    if resp.status_code == HTTPStatus.OK:
        return resp.output["embeddings"][0]["embedding"]
    else:
        print(resp)
