import base64
import os

from pydub import AudioSegment

from generalRequest import Gen_req_url
import json
import requests

APPId = "a69d6c98"
APISecret = "MzNhZWY0YTM0MzBkOWU4MDY5ZTVkMzNl"
APIKey = "542ef30748a29afb6837bab801610898"


def gen_create_group(group_id):
    body = {
        "header": {
            "app_id": APPId,
            "status": 3
        },
        "parameter": {
            "s782b4996": {
                "func": "createGroup",
                "groupId": group_id,
                "createFeatureRes": {
                    "encoding": "utf8",
                    "compress": "raw",
                    "format": "json"
                }
            }
        },
    }
    return body


def gen_create_feature(group_id, feature_id, voice_file_path):
    with open(voice_file_path, "rb") as f:
        audioBytes = f.read()
    body = {
        "header": {
            "app_id": APPId,
            "status": 3
        },
        "parameter": {
            "s782b4996": {
                "func": "createFeature",
                "groupId": group_id,
                "featureId": feature_id,
                "createFeatureRes": {
                    "encoding": "utf8",
                    "compress": "raw",
                    "format": "json"
                }
            }
        },
        "payload": {
            "resource": {
                "encoding": "lame",
                "sample_rate": 16000,
                "channels": 1,
                "bit_depth": 16,
                "status": 3,
                "audio": str(base64.b64encode(audioBytes), 'UTF-8')
            }
        }
    }
    return body


def gen_search_feature(group_id, voice_file_path):
    with open(voice_file_path, "rb") as f:
        audioBytes = f.read()
    body = {
        "header": {
            "app_id": APPId,
            "status": 3
        },
        "parameter": {
            "s782b4996": {
                "func": "searchFea",
                "groupId": group_id,
                "topK": 2,
                "searchFeaRes": {
                    "encoding": "utf8",
                    "compress": "raw",
                    "format": "json"
                }
            }
        },
        "payload": {
            "resource": {
                "encoding": "lame",
                "sample_rate": 16000,
                "channels": 1,
                "bit_depth": 16,
                "status": 3,
                "audio": str(base64.b64encode(audioBytes), 'UTF-8')
            }
        }
    }
    return body


def gen_delete_feature(group_id, feature_id):
    body = {
        "header": {
            "app_id": APPId,
            "status": 3

        },
        "parameter": {
            "s782b4996": {
                "func": "deleteFeature",
                "groupId": group_id,
                "featureId": feature_id,
                "deleteFeatureRes": {
                    "encoding": "utf8",
                    "compress": "raw",
                    "format": "json"
                }
            }
        }
    }
    return body


def gen_search_feature_list(group_id):
    body = {
        "header": {
            "app_id": APPId,
            "status": 3
        },
        "parameter": {
            "s782b4996": {
                "func": "queryFeatureList",
                "groupId": group_id,
                "queryFeatureListRes": {
                    "encoding": "utf8",
                    "compress": "raw",
                    "format": "json"
                }
            }
        }
    }
    return body


def gen_update_feature(group_id, feature_id, file_path):
    with open(file_path, "rb") as f:
        audioBytes = f.read()
        body = {
            "header": {
                "app_id": APPId,
                "status": 3
            },
            "parameter": {
                "s782b4996": {
                    "func": "updateFeature",
                    "groupId": group_id,
                    "featureId": feature_id,
                    "updateFeatureRes": {
                        "encoding": "utf8",
                        "compress": "raw",
                        "format": "json"
                    }
                }
            },
            "payload": {
                "resource": {
                    "encoding": "lame",
                    "sample_rate": 16000,
                    "channels": 1,
                    "bit_depth": 16,
                    "status": 3,
                    "audio": str(base64.b64encode(audioBytes), 'UTF-8')
                }
            }
        }
    return body


def req_url(service, group_id=None, feature_id=None, file_path=None):
    """
    开始请求
    :param service: 服务名称['create feature','search feature','create group','delete feature']
    :param group_id: 组名
    :param feature_id: 声纹名
    :param file_path: body里的文件路径
    :return:
    """

    gen_req_url = Gen_req_url()
    if service == 'create feature':
        file_path = convert_wav_to_mp3(file_path)
        body = gen_create_feature(group_id, feature_id, file_path)
    elif service == 'create group':
        body = gen_create_group(group_id)
    elif service == 'search feature':
        file_path = convert_wav_to_mp3(file_path)
        body = gen_search_feature(group_id, file_path)
    elif service == 'delete feature':
        body = gen_delete_feature(group_id, feature_id)
    elif service == 'feature list':
        body = gen_search_feature_list(group_id)
    elif service == 'update feature':
        file_path = convert_wav_to_mp3(file_path)
        body = gen_update_feature(group_id, feature_id, file_path)
    else:
        raise Exception("The [service] parameter is invalid")

    request_url = gen_req_url.assemble_ws_auth_url(requset_url='https://api.xf-yun.com/v1/private/s782b4996',
                                                   method="POST", api_key=APIKey, api_secret=APISecret)

    headers = {'content-type': "application/json", 'host': 'api.xf-yun.com', 'appid': '$APPID'}
    response = requests.post(request_url, data=json.dumps(body), headers=headers)
    tempResult = json.loads(response.content.decode('utf-8'))
    print(tempResult)
    # result = decode_base64_to_dict(tempResult['payload']['searchFeaRes']['text'])
    # print('current speaker: ', result['scoreList'][0]['featureId'])
    # return result['scoreList'][0]['featureId']
    return result_analysis(tempResult, service)


def result_analysis(result, service):
    header = result['header']
    if header['code'] != 0:
        print('speaker recognition failed')
        return ''
    body = result['payload']
    if service == 'create feature':
        text = body['createFeatureRes']['text']
    elif service == 'create group':
        text = body['createGroupRes']['text']
    elif service == 'search feature':
        text = body['searchFeaRes']['text']
    elif service == 'delete feature':
        text = body['deleteFeatureRes']['text']
    elif service == 'feature list':
        text = body['queryFeatureListRes']['text']
    elif service == 'update feature':
        text = body['updateFeatureRes']['text']
    else:
        raise Exception("The [service] parameter is invalid")
    message = decode_base64_to_dict(text)
    if service == 'search feature':
        top_feature = message['scoreList'][0]
        top_score = top_feature['score']
        top_feature_id = top_feature['featureId']
        return top_feature_id, top_score
    elif service == 'feature list':
        return message
    else:
        return 'success'


def convert_wav_to_mp3(input_wav_path, output_mp3_path=None, bitrate="16k"):
    """
    将 WAV 文件转换为 MP3 文件

    参数:
        input_wav_path (str): 输入的 WAV 文件路径
        output_mp3_path (str): 输出的 MP3 文件路径（可选，默认与输入同目录）
        bitrate (str): 输出的比特率，默认为 "192k"
    """
    # 如果没有指定输出路径，则使用输入文件相同目录，仅修改扩展名
    if output_mp3_path is None:
        output_mp3_path = input_wav_path.rsplit('.', 1)[0] + '.mp3'

    # 加载 WAV 文件
    audio = AudioSegment.from_wav(input_wav_path)

    # 导出为 MP3
    audio.export(output_mp3_path, format="mp3", bitrate=bitrate)

    print(f"转换成功: {input_wav_path} -> {output_mp3_path}")
    return output_mp3_path


def decode_base64_to_dict(base64_str):
    """
    将base64字符串解码为字典
    """
    # 将base64字符串转换为字节
    base64_bytes = base64_str.encode('utf-8')
    # 进行base64解码
    bytes_data = base64.b64decode(base64_bytes)
    # 将字节转换为字符串
    json_str = bytes_data.decode('utf-8')
    # 将JSON字符串转换为字典
    return json.loads(json_str)


if __name__ == '__main__':
    file_path1 = '../huangpu.wav'
    # req_url service取值:
    # 1.创建声纹特征库 create group
    # 2.添加音频特征 create feature
    # 3.查询特征列表 feature list
    # 4.特征比对1:N search feature
    # 5.更新音频特征 updateFeature
    # 6.删除指定特征 delete feature
    # req_url('feature list', 'home')
    result = req_url('feature list', 'home')
    print(result)
