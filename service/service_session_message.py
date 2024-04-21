from db_api.api.api_pinecone import query
from db_api.models import ChatSession, Message, VectorBaseInfo
from db_api.api.api_embedding import get_single_embedding
from db_api.api.api_qwen import call_stream_with_messages
import db_api.sqlite as db


# 获取所有会话,会话信息包括 id ， name, end_time
def get_all_chat_session():
    chat_sessions = db.get_all_chat_session()
    chat_session_info = [{'id': chat_session.id, 'name': chat_session.name,
                          'end_time': chat_session.end_time} for chat_session in chat_sessions]

    return chat_session_info

# 获取会话对应的对话内容


# def get_messages_by_chat_session_id(chat_session_id):
#     # 获取指定ID的会话
#     chat_session = chat_session.objects.get(id=chat_session_id)

#     # 获取该会话的所有信息
#     messages = Message.objects.filter(
#         chat_session=chat_session).order_by('time')

#     # 获取每个消息的角色与内容
#     message_info = [{'role': message.role, 'content': message.content}
#                     for message in messages]
#     return message_info


# # 创建chat_session
# def create_chat_session():
#     chat_session = chat_session()
#     chat_session.name = timezone.now().strftime(
#         "%Y-%m-%d %H:%M:%S")  # 使用当前时间作为会话名，格式为"年-月-日 时:分:秒"
#     chat_session.save()  # 保存会话到数据库
#     return chat_session


# # 删除会话
# def delete_chat_session_by_chat_session_id(chat_session_id):
#     chat_session = chat_session.objects.get_or_create(id=chat_session_id)
#     chat_session.delete()


# # 更新会话名字
# def update_name_by_chat_session_id(chat_session_id, chat_session_name):
#     # 获取指定ID的会话
#     chat_session = chat_session.objects.get(id=chat_session_id)
#     # 更新会话名字
#     chat_session.name = chat_session_name
#     # 保存会话
#     chat_session.save()

# # 更新会话结束时间


# def update_end_time_by_chat_session_id(chat_session_id):
#     # 获取指定ID的会话
#     chat_session = chat_session.objects.get(id=chat_session_id)

#     # 更新会话结束时间
#     chat_session.end_time = timezone.now()

#     # 保存会话
#     chat_session.save()

# 数字转英文
def number_to_words(n):
    num_to_word = {
        1: 'one',
        2: 'two',
        3: 'three',
        4: 'four',
        5: 'five',
        6: 'six',
        7: 'seven',
        8: 'eight',
        9: 'nine',
        10: 'ten'
    }
    return num_to_word.get(n, 'Number out of range')

# 利用知识库构建带有提示词内容


def query_integrate_content(content: str, vector_name):
    # 获取输入文本对应向量
    content_embedding = get_single_embedding(content)
    # 获取相关文本列表
    text_list = query(vector_name, content_embedding)
    prompt = ""
    i = 1
    for text in text_list:
        prompt += "This is the "+number_to_words(i)+" information:"+text + "//"
        i += 1

    # 构建输入内容
    content = f'''
    You are a helpful assistant,
    This is my question:
    {content}
    The following is relevant information. 
    Please combine it with my question and decide whether to reply based on the relevant information:
    {prompt}
    '''
    print("\n\ncontent:", content)

    return content


# 与千问对话  ！！！保存对话时，不带提示词，输入到模型的是带提示词的内容
def talk_stream_with_qwen(chat_session_id, vectorbase_name, messages: list):
    input_content = messages[-1]['content']
    print("input_text:", input_content)
    # 创建新的消息
    message = Message(chat_session_id=chat_session_id,
                      role='user', content=input_content)
    # 保存当前消息,但不带提示词存入数据库
    db.save_message_by_chat_session_id(message=message)

    # 选定知识库，则根据知识库构建内容
    if vectorbase_name != "None":
        input_content = query_integrate_content(
            content=input_content,
            vector_name=vectorbase_name
        )

    # 构建messages 输入到LLM的内容，带有提示词
    messages.append({
        'role': 'user',
        'content': input_content
    })
    # 向qwenAPI发送请求并流式输出
    stream_gen = call_stream_with_messages(chat_session_id, messages)

    # 返回流响应流
    return stream_gen
