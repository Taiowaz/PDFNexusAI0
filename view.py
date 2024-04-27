import datetime
import os
import shutil
import time
import gradio as gr
from matplotlib.pyplot import sca
import service.service_pdf_vectorbase as pv
import service.service_session_message as sm
import threading

# 消息记录
messages = []

# 定义输入框内容
input_text = ""


""" 相关函数 """
# 获取知识库信息列表


def get_knowledge_base_info() -> list:
    vectorbase_names = [vectorbaseinfo['name']
                        for vectorbaseinfo in pv.get_all_vector_base()]
    vectorbase_names.insert(0, "None")
    return vectorbase_names

# 创建知识库信息或解析PDF文件


def create_knowledgebase_info_or_parse_pdf_file(knowledgebase_name, files):
    knowledgebase_name = str(knowledgebase_name).strip()
    # 上传文件组件值
    file_upload_pdf_value = []
    if knowledgebase_name == "None":
        gr.Warning("Please choose or create a knowledge base")
        file_upload_pdf_value = files
    else:
        if not pv.vector_base_exists(knowledgebase_name):
            pv.create_vectorbase_info_db(knowledgebase_name)
        gr.Info("Processing...")
        # 创建文件夹
        pdf_folder = "file/temp/" + \
            str(datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
        os.makedirs(pdf_folder, exist_ok=True)  # 忽略已存在的文件夹导致的异常
        # 保存文件
        for file in files:
            # 获取文件名
            base_name = os.path.basename(file)
            # 创建目标文件的路径
            dest_file = os.path.join(pdf_folder, base_name)
            # 保存文件
            shutil.copyfile(file, dest_file)
        # 异步对文件进行处理
        event_end_parse_pdf = threading.Event()
        thread_parse_pdf = threading.Thread(
            target=pv.process_pdf_vectorbase_in_threads,
            args=(knowledgebase_name, pdf_folder, event_end_parse_pdf)
        )
        thread_parse_pdf.start()
        event_end_parse_pdf.wait()
        # 完成提示
        gr.Info("Done")

    """ 返回一个组件才能更新组件 """
    return (
        gr.Dropdown(
            choices=get_knowledge_base_info(),
            interactive=True,
            value=knowledgebase_name,
            scale=3,
            show_label=False,
            allow_custom_value=False,
        ),
        gr.Dropdown(
            choices=get_knowledge_base_info(),
            label="Choose or Create Knowledge Base and Upload PDF Report to the Knowledge Base",
            value=knowledgebase_name,
            scale=8,
            interactive=True,
            allow_custom_value=True,
        ),
        file_upload_pdf_value,
        gr.MultimodalTextbox(
            interactive=True,
            file_types=["pdf"],
            placeholder="Please input something...",
            show_label=False,
        )
    )


# 将用户输入立刻更新到chat界面中
def update_input_text(user_input, chat_history):
    user_msg = str(user_input["text"]).strip()
    # 用户输入不为空时，才发送到LLM
    if user_msg != "":
        chat_history += [[user_msg, None]]
    else:
        gr.Warning("Please input something")
    return {"text": "", "files": None}, chat_history

# 模型回应


def bot_resp(knowledgebase_name, chat_history):
    knowledgebase_name = str(knowledgebase_name).strip()
    # 构建消息记录 用于LLM输入
    input_text = chat_history[-1][0]
    message = {
        'role': 'user',
        'content': input_text
    }
    messages.append(message)
    bot_resp_stream = sm.talk_stream_with_qwen(
        chat_session_id=1,
        vectorbase_name=knowledgebase_name,
        messages=messages
    )

    chat_history[-1][1] = ""
    for resp_incre in bot_resp_stream:
        # 千问API流式输出是以多个字符增量返回的，为便于用户阅读，按字符流式输出
        for char in resp_incre:
            chat_history[-1][1] += char
            time.sleep(0.05)
            yield chat_history
    # 将LLM回应内容加入到信息历史中
    messages.append(
        {
            'role': 'assistant',
            'content': chat_history[-1][1]
        }
    )


""" 构建界面 """
with gr.Blocks(
    title="PDFNexusAI",
    theme=gr.themes.Soft(
        spacing_size=gr.themes.sizes.spacing_sm,
        text_size=gr.themes.sizes.text_sm,
        radius_size=gr.themes.sizes.radius_md,
    ),
    fill_height=True,
    delete_cache=(60, 60)
) as demo:
    # 显示项目名称
    gr.Markdown("# PDFNexusAI")
    # Chat对话界面
    with gr.Tab("ChatBot"):
        with gr.Column():
            # 显示聊天记录
            chatbot = gr.Chatbot(
                bubble_full_width=False,
                placeholder="Talking with Chatbot...",
            )
            # 输入框
            with gr.Group():
                # 选择知识库
                dropdown_kb_input = gr.Dropdown(
                    label="Choose Knowledge Base",
                    choices=get_knowledge_base_info(),
                    interactive=True,
                    value=0,
                    allow_custom_value=False,
                )
                # 输入文本
                user_input = gr.MultimodalTextbox(
                    interactive=True,
                    file_types=["pdf"],
                    placeholder="Please input something...",
                    show_label=False,
                )
                input_text_submit = user_input.submit(
                    fn=update_input_text,
                    inputs=[user_input, chatbot],
                    outputs=[user_input, chatbot],
                    queue=False
                ).then(
                    fn=bot_resp,
                    inputs=[dropdown_kb_input, chatbot],
                    outputs=[chatbot]
                )
    with gr.Tab("ChatSession"):
        gr.Markdown("## Chat Session")
    # 知识库构建界面
    with gr.Tab("Knowledge Base"):
        gr.Markdown("## Build Your Own Knowledge Base")
        with gr.Column():
            with gr.Row():
                dropdown_kb_upload = gr.Dropdown(
                    choices=get_knowledge_base_info(),
                    label="Choose or Create Knowledge Base and Upload PDF Report to the Knowledge Base",
                    scale=8,
                    value=0,
                    interactive=True,
                    allow_custom_value=True,
                )
                button_upload_pdf = gr.Button(
                    value="save",
                    variant="primary",
                    scale=2
                )
            # 上传 PDF 文件
            file_upload_pdf = gr.File(
                value=[],
                file_count='multiple',
                label="Upload PDF File",
                scale=7,
                file_types=['pdf'],
                type='filepath',
            )
            # PDF文件处理函数绑定
            button_upload_pdf.click(
                fn=create_knowledgebase_info_or_parse_pdf_file,
                inputs=[dropdown_kb_upload, file_upload_pdf],
                # 在加载时，将按钮与相关输入禁用
                outputs=[dropdown_kb_input, dropdown_kb_upload,
                         file_upload_pdf, user_input]
            )

# 启动界面
demo.queue()
demo.launch()
