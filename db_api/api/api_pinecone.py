from pinecone import Pinecone
import uuid
pc = Pinecone()

# 创建向量库


def create_vectorbase(vector_name: str):
    pc.create_index(index_name=vector_name, metric='cosine', shards=1)

    print(f'Vectorbase {vector_name} created successfully.')

# 插入文本与向量组合列表


def upsert(index_name: str, text_embedding_list: list):
    index = pc.Index(index_name)
    vector_list = []
    for text_embedding in text_embedding_list:
        vector = {
            "id": str(uuid.uuid4()),
            "values": text_embedding["embedding"],
            "metadata": {
                "text": text_embedding["text"],
            }
        }
        vector_list.append(vector)
    index.upsert(vector_list)

# 查询相关向量对应的文本列表


def query(index_name: str, vector: list) -> list:
    index = pc.Index(index_name)
    rsp = index.query(
        vector=vector,
        top_k=6,
        include_metadata=True,
        include_values=False,
    )
    text_list = [res.metadata['text'] for res in rsp.matches]
    return text_list
