# -*- coding: utf-8 -*-

import sys
import json

# sys.path.append("../..")
from common import credential
from asr import flash_recognizer


def recognize_audio_file(audio_path, engine_type="16k_zh"):
    """
    使用腾讯云语音识别API识别音频文件

    Args:
        audio_path (str): 音频文件路径
        engine_type (str): 引擎类型，默认为"16k_zh"

    Returns:
        dict: 包含识别结果和状态信息的字典
    """
    APPID = "1301020683"
    SECRET_ID = "AKIDMabQ1OYUDiCXigU7WgeYFixeAXgbJp8C"
    SECRET_KEY = "tY1HJ9oGcjcHhwzoPuCF5g5II3bv3zlO"


    try:
        # 初始化凭证和识别器
        credential_var = credential.Credential(SECRET_ID, SECRET_KEY)
        recognizer = flash_recognizer.FlashRecognizer(APPID, credential_var)

        # 配置识别请求
        req = flash_recognizer.FlashRecognitionRequest(engine_type)
        req.set_filter_modal(0)
        req.set_filter_punc(0)
        req.set_filter_dirty(0)
        req.set_voice_format("wav")
        req.set_word_info(0)
        req.set_convert_num_mode(1)

        # 读取并识别音频文件
        with open(audio_path, 'rb') as f:
            audio_data = f.read()
            result_data = recognizer.recognize(req, audio_data)
            resp = json.loads(result_data)

            # 检查识别结果
            if resp["code"] != 0:
                return {
                    "success": False,
                    "request_id": resp.get("request_id", ""),
                    "code": resp["code"],
                    "message": resp.get("message", "Unknown error"),
                    "result": None
                }

            # 提取识别文本
            texts = []
            for channel_result in resp.get("flash_result", []):
                texts.append({
                    "channel_id": channel_result.get("channel_id", 0),
                    "text": channel_result.get("text", "")
                })

            return {
                "success": True,
                "request_id": resp.get("request_id", ""),
                "result": texts
            }

    except FileNotFoundError:
        return {
            "success": False,
            "message": f"Audio file not found: {audio_path}",
            "result": None
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Recognition failed: {str(e)}",
            "result": None
        }


def speech_recognition(file_path):
    result = recognize_audio_file(file_path)
    if result["success"]:
        print("Recognition successful!")
        print(f"Request ID: {result['request_id']}")
        for item in result["result"]:
            print(f"Channel {item['channel_id']}: {item['text']}")
        return result["result"][0]['text']
    else:
        print("Recognition failed!")
        print(f"Error: {result.get('message', 'Unknown error')}")
        if "code" in result:
            print(f"Error code: {result['code']}")
        return None


# 使用示例
if __name__ == "__main__":
    # 配置信息
    AUDIO_FILE = "segment_recording/20250528_011458_segment_1.wav"

    # 调用函数进行识别
    result = recognize_audio_file(AUDIO_FILE)

    if result["success"]:
        print("Recognition successful!")
        print(f"Request ID: {result['request_id']}")
        for item in result["result"]:
            print(f"Channel {item['channel_id']}: {item['text']}")
    else:
        print("Recognition failed!")
        print(f"Error: {result.get('message', 'Unknown error')}")
        if "code" in result:
            print(f"Error code: {result['code']}")
