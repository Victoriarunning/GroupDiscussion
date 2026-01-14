import re
from statement_keeper import add_statement
from qwenAPI import QwenAPI


# 初始化Qwen API客户端
qwen_client = QwenAPI(model="qwen-max")


# 请求模型，并将结果输出
def get_answer(user_input):
    """
    使用Qwen大模型获取回答

    Args:
        user_input (str): 用户输入的问题或对话内容

    Returns:
        str: 模型生成的回答
    """
    try:
        text = qwen_client.ask(user_input)
        print(text)
        return text
    except Exception as e:
        raise Exception(f"Interaction recognition failed: {e}")


def parse_reply_objects(text):
    """
    解析给定的文本，提取每行中“回复对象”后的名称。

    参数:
        text (str): 包含多行文本的字符串，每行格式为“回复对象：XXX”。

    返回:
        list: 包含每行回复对象名称的列表，未指定时为None。
    """
    # 将文本按行分割
    lines = text.strip().split('\n')

    # 定义正则表达式模式，匹配“回复对象：名称”或“回复对象：无”
    pattern = re.compile(r'回复对象：(无|[^\s]+)')

    # 初始化结果列表
    reply_objects = []

    for line in lines:
        match = pattern.search(line)
        if match:
            group = match.group(1)
            # 如果匹配到“无”，则添加None，否则添加匹配的名称
            reply_objects.append(group)
        else:
            # 如果某行不匹配预期格式，可以选择添加None或其他处理方式
            reply_objects.append(None)

    return reply_objects


def get_prompt_word():
    return "" \
           "请分析上述若干条对话，我需要知道说话人的每句话是否是在回复其他人，回复对象是谁，按以下格式返回结果\
            1、回复对象：\
            2、回复对象：\
            。。。\
            注意：回复对象只有具体某一个人和无两种可能，不需要给出理由和解析"


def interaction_recognition(formatted_text, raw_statement):
    complete_statement = formatted_text + "\n" + get_prompt_word()
    new_statement = complete_statement.replace('&', ':')
    # 开始输出模型内容
    text = get_answer(new_statement)
    print(text)
    reply_objects = parse_reply_objects(text)
    for i, (raw_text, reply_obj) in enumerate(zip(raw_statement, reply_objects)):
        add_statement(raw_text + '&' + reply_obj)
    print(reply_objects)


# 主程序入口
if __name__ == '__main__':
    Input = "" \
            "1、崔童：对，我们开始吧，拆这笔有的第一个讨论数据类型。\
            2、崔童：我们已经开始了，可以开始直接开始了。\
            3、崔童：就志伟不是不用了，志伟他们来不了。\
            4、崔童：就你们觉得有现在有哪几种数据类型，就是我们常见的。\
            5、孙一平：分类数据空间数据说话说大点去分类数据、空间数据啊，持续数据，还有多变量数据。\
            6、上青：呃，分类数据是什么个定义？\
            7、孙一平：就是说按类别分，就是我们用手机的话是用 iPhone 的还是用安卓的。\
            8、孙一平：就是说它有多个类别标签的对数据啊。从那个数据的特征上我觉得可以分成高维数据额，还有比如说时序数据额、时空数据啊。\
            9、崔童：那就把就是那个什么刚才说过的一些数据类型，我们就是详细讨论一下它每种类型的一个特点。\
            10、淳熙：特点，比方说，嗯，高危数据的特点可能就是考核数据就是位数很高，所以的话。\
            11、孙一平：就是说这个高危数据它比较抽象，不好理解，不像我们二维的一些相关的一些这个变量比较好理解它的关系。\
            12、孙一平：那高维数据具有很多个属性值，它们之间的关系很难通过统计，普通的统计方法或者说一些可视化图表进行这个理解。\
            13、孙一平：所以针对这一类数据类型可能要复杂，就是要设计更加针对性的一些图表，比如说一些矩阵，或者说是散点图来进行这样的理解和探索，就是它更加复杂。\
            请分析上述若干条对话，我需要知道说话人的每句话是否是在回复其他人，回复对象是谁，按以下格式返回结果\
            1、回复对象：\
            2、回复对象：\
            。。。\
            注意：回复对象只有具体某一个人和无两种可能，不需要给出理由和解析"
    # 开始输出模型内容
    answer = get_answer(Input)
    reply_object = parse_reply_objects(answer)
    print(reply_object)
