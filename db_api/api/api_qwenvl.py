import dashscope

# 导入通义千问VL模型，用于图像识别
from dashscope import MultiModalConversation



def vision_completion(image_path: str) -> str:     # image_path: str这种语法被称为类型注解（Type Annotation）。
    messages = [                                   # image_path是变量名，str是该变量的预期类型，即字符串。                            
        {
            "role": "user",
            "content": [
                {
                    "image": "file://"+image_path
                    },
                {
                    "text":"What is in this image? Please describe the content of this image in concise English text.I just need you to return the description text and not to locate the specific content within the image."
                },
                {
                    "text":"Please return me a text of about 300 words."
                }

            ]
        }
    ]
    response = MultiModalConversation.call(model="qwen-vl-max",
                                           messages=messages,
                                           max_length=500) 
    with open("file/test/qwenvl.txt", "w+") as f:
        f.write(str(response)+"\n\n")
    return response.output.choices[0].message.content[0]["text"]; # 返回识别结果

