from dashscope import Generation
from dashscope.api_entities.dashscope_response import Role
from http import HTTPStatus
import random
import db_api.sqlite as db
from db_api.models import Message

# 普通回复
# 用于判定是否需要查询知识库
# 以及对知识库进行描述


def call_qwen(messages: list) -> str:
    resp = Generation.call(
        model=Generation.Models.qwen_max,
        messages=messages,
        # 设置返回结果为message格式
        result_format='message',
    )

    if resp.status_code == HTTPStatus.OK:
        return resp.output.choices[0]['message']['content']
    else:
        print("\nError: ", resp)


# 流式输出回复


def call_stream_with_messages(chat_session_id, messages: list):
    # 生成器函数
    def stream():
        resps = Generation.call(
            model=Generation.Models.qwen_max,
            messages=messages,
            seed=random.randint(1, 10000),      # 设置随机种子，保证此次流式输出不变
            result_format='message',
            stream=True,
            temperature=0.01,       # 设置输出随意度
            output_in_full=False,     # 每次输出增量
        )

        content = ""
        for resp in resps:
            if resp.status_code == HTTPStatus.OK:
                content_incre = resp.output.choices[0]['message']['content']
                content += content_incre
                with open("file/test/qwen.txt", "w+") as f:
                    f.write(str(resp)+"\n\n")
                yield content_incre
        # 存储到数据库中
        message = Message(
            account="test",
            chat_session_id=chat_session_id,
            role='assistant',
            content=content
        )
        db.save_message_by_chat_session_id(message=message)

    # 返回生成器
    return stream()
