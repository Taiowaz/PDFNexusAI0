import tempfile
import os
from unstructured.partition.pdf import partition_pdf
from unstructured.partition.utils.constants import PartitionStrategy
from unstructured.cleaners.core import clean, group_broken_paragraphs
from unstructured.chunking.title import chunk_by_title
from unstructured .documents.elements import (
    Header,
    Footer,
    Image,
    CompositeElement,
    Table
)

from db_api.api.api_qwenvl import vision_completion

# 分解单个pdf报告


def parse_pdf(filename: str) -> list:
    """ 分割并获取元素 """
    elements = partition_pdf(
        filename=filename,
        strategy=PartitionStrategy.HI_RES,
        extract_images_in_pdf=True,
        extract_image_block_types=["Image", "Table"],
        extract_image_block_to_payload=False,
        extract_image_block_output_dir=tempfile.gettempdir()
    )

    """  清洗页头页脚 """
    filtered_elements = [
        element
        for element in elements
        if not (isinstance(element, Header) or isinstance(element, Footer))
    ]

    min_image_width = 250
    min_image_height = 270

    """ 对文本进行清洗，图像转换为描述性文本 """
    for element in filtered_elements:
        if element.text != "":
            element.text = group_broken_paragraphs(element.text)
            element.text = clean(
                element.text,
                bullets=False,
                extra_whitespace=True,
                dashes=False,
                trailing_punctuation=False
            )
        elif isinstance(element, Image):
            point1 = element.metadata.coordinates.points[0]
            point2 = element.metadata.coordinates.points[2]
            width = abs(point2[0]-point1[0])
            height = abs(point2[1]-point1[1])
            if width >= min_image_width and height >= min_image_height:
                element.text = vision_completion(element.metadata.image_path)

    """ 进行分块 """
    chunks = chunk_by_title(
        elements=filtered_elements,
        multipage_sections=True,
        combine_text_under_n_chars=0,
        new_after_n_chars=None,
        max_characters=4096,
    )

    text_list = []

    for chunk in chunks:  # 遍历分块，获取文本列表
        if isinstance(chunk, CompositeElement):
            text = chunk.text
            text_list.append(text)
        elif isinstance(chunk, Table):  # 表格转换为html
            if chunk.metadata.text_as_html is not None:
                if text_list:  # 列表不为空
                    text_list[-1] = text_list[-1] + \
                        ":" + chunk.metadata.text_as_html        # 用冒号进行分隔标题与表格，防止与批量转换向量的换行符冲突
                else:
                    text_list.append(chunk.metadata.text_as_html)

    # 将文字中的换行符替换为空格，防止与批量转换向量的换行符冲突
    text_list = [text.replace("\n", "//") for text in text_list]
    # 打印日志
    print(f"\nParsed: {filename}\n")
    return text_list

# 分解文件夹内多个pdf报告


def parse_pdflist(dir: str) -> list:
    files = os.listdir(dir)
    text_list = []
    for file_name in files:
        file_path = os.path.join(dir, file_name)
        text_list.extend(parse_pdf(file_path))
    return text_list
