from dashscope import Generation
from dashscope.api_entities.dashscope_response import Role
from http import HTTPStatus
import random

import db_api.sqlite as db

from db_api.models import Message


def get_reply(input: str, relative_text: list) -> str:
    # 构建相关文本
    context = '\n'.join(relative_text)
    # 构建提示词与问题
    prompt = f'''请结合```内的内容回答问题。"
    ```
    {context}
    ```
    我的问题是：{input}。
    '''

    messages = [
        {'role': Role.SYSTEM, 'content': 'You are a helpful assistant, please return appropriate output based on the input.'},
        {'role': Role.USER, 'content': prompt}
    ]

    resp = Generation.call(
        model=Generation.Models.qwen_max,
        messages=messages,
        # 设置返回结果为message格式
        result_format='message',
    )

    if resp.status_code == HTTPStatus.OK:
        print(resp.output.choices[0]['message']['content'])
        # 添加记录到messages中
        messages.append(
            {
                'role': resp.output.choices[0]['message']['role'],
                'content': resp.output.choices[0]['message']['content']
            }
        )
    else:
        return "error"

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
