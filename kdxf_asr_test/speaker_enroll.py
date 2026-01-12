import base64

from generalRequest import Gen_req_url
import json
import requests


def gen_create_group():
    body = {
        "header": {
            "app_id": APPId,
            "status": 3
        },
        "parameter": {
            "s782b4996": {
                "func": "createGroup",
                "groupId": "home",
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


def req_url(APPId, APIKey, APISecret, file_path=None):
    """
    开始请求
    :param APPId: APPID
    :param APIKey:  APIKEY
    :param APISecret: APISecret
    :param file_path: body里的文件路径
    :return:
    """
    gen_req_url = Gen_req_url()
    body = gen_search_feature("home", "target.mp3")
    request_url = gen_req_url.assemble_ws_auth_url(requset_url='https://api.xf-yun.com/v1/private/s782b4996', method="POST", api_key=APIKey, api_secret=APISecret)

    headers = {'content-type': "application/json", 'host': 'api.xf-yun.com', 'appid': '$APPID'}
    response = requests.post(request_url, data=json.dumps(body), headers=headers)
    tempResult = json.loads(response.content.decode('utf-8'))
    print(tempResult)


if __name__ == '__main__':
    APPId = "a69d6c98"
    APISecret = "MzNhZWY0YTM0MzBkOWU4MDY5ZTVkMzNl"
    APIKey = "542ef30748a29afb6837bab801610898"
    file_path = '示例音频/讯飞开放平台.mp3'
    # apiname取值:
    # 1.创建声纹特征库 createGroup
    # 2.添加音频特征 createFeature
    # 3.查询特征列表 queryFeatureList
    # 4.特征比对1:1 searchScoreFea
    # 5.特征比对1:N searchFea
    # 6.更新音频特征 updateFeature
    # 7.删除指定特征 deleteFeature
    # 8.删除声纹特征库 deleteGroup
    req_url(APPId=APPId, APIKey=APIKey, APISecret=APISecret, file_path=file_path)
