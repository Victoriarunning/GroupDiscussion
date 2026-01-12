# -*- encoding:utf-8 -*-
import hashlib
import hmac
import base64
import json
import time
import threading
import urllib.parse
import logging
import uuid
from websocket import create_connection, WebSocketException
import websocket
import datetime

# 新增：音频采集依赖
import pyaudio

# ==================== 全局配置 ====================
FIXED_PARAMS = {
    "audio_encode": "pcm_s16le",
    "lang": "autodialect",
    "samplerate": "16000"
}
AUDIO_FRAME_SIZE = 1280      # 每帧字节数（16k采样率 × 2字节 × 0.04秒 = 1280）
FRAME_INTERVAL_MS = 40       # 每40ms发送一帧

CHUNK = AUDIO_FRAME_SIZE     # 每次录音字节数
FORMAT = pyaudio.paInt16     # 16bit位深
CHANNELS = 1                 # 单声道
RATE = 16000                 # 采样率16k


class RTASRClient():
    def __init__(self, app_id, access_key_id, access_key_secret):
        self.app_id = app_id
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
        self.base_ws_url = "wss://office-api-ast-dx.iflyaisol.com/ast/communicate/v1"
        self.ws = None
        self.is_connected = False
        self.recv_thread = None
        self.session_id = None
        self.is_recording = False  # 控制录音状态
        self.audio_interface = None
        self.audio_stream = None

    def _generate_auth_params(self):
        """生成鉴权参数"""
        auth_params = {
            "accessKeyId": self.access_key_id,
            "appId": self.app_id,
            "uuid": uuid.uuid4().hex,
            "utc": self._get_utc_time(),
            **FIXED_PARAMS
        }

        sorted_params = dict(sorted([
            (k, v) for k, v in auth_params.items()
            if v is not None and str(v).strip() != ""
        ]))
        base_str = "&".join([
            f"{urllib.parse.quote(k, safe='')}={urllib.parse.quote(v, safe='')}"
            for k, v in sorted_params.items()
        ])

        signature = hmac.new(
            self.access_key_secret.encode("utf-8"),
            base_str.encode("utf-8"),
            hashlib.sha1
        ).digest()
        auth_params["signature"] = base64.b64encode(signature).decode("utf-8")
        return auth_params

    def _get_utc_time(self):
        beijing_tz = datetime.timezone(datetime.timedelta(hours=8))
        now = datetime.datetime.now(beijing_tz)
        return now.strftime("%Y-%m-%dT%H:%M:%S%z")

    def connect(self):
        """建立WebSocket连接"""
        try:
            auth_params = self._generate_auth_params()
            params_str = urllib.parse.urlencode(auth_params)
            full_ws_url = f"{self.base_ws_url}?{params_str}"
            print(f"【连接信息】完整URL：{full_ws_url}")

            self.ws = create_connection(
                full_ws_url,
                timeout=15,
                enable_multithread=True
            )
            self.is_connected = True
            print("【连接成功】WebSocket握手完成，等待服务端就绪...")
            time.sleep(1.5)

            self.recv_thread = threading.Thread(target=self._recv_msg, daemon=True)
            self.recv_thread.start()
            return True
        except WebSocketException as e:
            print(f"【连接失败】WebSocket错误：{str(e)}")
            return False
        except Exception as e:
            print(f"【连接异常】其他错误：{str(e)}")
            return False

    def _recv_msg(self):
        """接收服务端消息"""
        while self.is_connected:
            if not self.ws:
                break
            try:
                msg = self.ws.recv()
                if not msg:
                    print("【接收消息】服务端关闭连接")
                    break

                if isinstance(msg, str):
                    try:
                        msg_json = json.loads(msg)
                        print(f"【接收消息】{msg_json}")
                        if (msg_json.get('msg_type') == 'action' 
                            and 'sessionId' in msg_json.get('data', {})):
                            self.session_id = msg_json['data']['sessionId']
                    except json.JSONDecodeError:
                        print(f"【接收异常】非JSON文本消息：{msg[:50]}...")
                else:
                    pass  # 忽略二进制数据
            except Exception as e:
                if self.is_connected:
                    print(f"【接收异常】{str(e)}")
                break
        print("【接收线程】已退出")

    def start_microphone_streaming(self, max_duration=60):
        """
        开始从麦克风实时录音并发送
        :param max_duration: 最大录音时长（秒），默认60秒
        """
        if not self.is_connected:
            print("【发送失败】WebSocket未连接")
            return False

        self.audio_interface = pyaudio.PyAudio()
        try:
            self.audio_stream = self.audio_interface.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK // 2  # 注意：pyaudio以sample为单位，不是byte
            )
            print("【麦克风】录音流已打开，开始采集...")

            self.is_recording = True
            frame_index = 0
            start_time = time.time()

            print(f"【开始发送】每{FRAME_INTERVAL_MS}ms发送一帧，持续中...")

            while self.is_recording:
                # 动态控制节奏：每40ms发一次
                expected_time = start_time + (frame_index * FRAME_INTERVAL_MS / 1000)
                current_time = time.time()
                sleep_time = expected_time - current_time
                if sleep_time > 0:
                    time.sleep(sleep_time)

                # 录音并发送
                try:
                    audio_data = self.audio_stream.read(CHUNK // 2, exception_on_overflow=False)
                    if len(audio_data) != CHUNK:
                        print(f"⚠️  帧长度异常：期望{CHUNK}，实际{len(audio_data)}")
                    self.ws.send_binary(audio_data)
                    frame_index += 1
                except Exception as e:
                    print(f"【录音异常】{str(e)}")
                    break

                # 超时保护
                if time.time() - start_time > max_duration:
                    print(f"【自动停止】达到最大时长 {max_duration} 秒")
                    self.is_recording = False

            # 发送结束标记
            end_msg = {"end": True}
            if self.session_id:
                end_msg["sessionId"] = self.session_id
            self.ws.send(json.dumps(end_msg, ensure_ascii=False))
            print(f"【发送结束】已发送结束标记：{end_msg}")

        except Exception as e:
            print(f"【麦克风错误】{str(e)}")
            return False
        finally:
            self._cleanup_audio()

    def _cleanup_audio(self):
        """清理音频资源"""
        if self.audio_stream:
            self.audio_stream.stop_stream()
            self.audio_stream.close()
        if self.audio_interface:
            self.audio_interface.terminate()

    def stop(self):
        """外部调用停止录音"""
        self.is_recording = False

    def close(self):
        """安全关闭连接"""
        self.is_recording = False
        if self.is_connected and self.ws:
            self.is_connected = False
            try:
                if self.ws.connected:
                    self.ws.close(status=1000, reason="客户端正常关闭")
                print("【连接关闭】WebSocket已安全关闭")
            except Exception as e:
                print(f"【关闭异常】{str(e)}")
        self._cleanup_audio()


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    logging.getLogger("websocket").setLevel(logging.WARNING)

    # ========== ⚙️ 配置参数 ==========
    APP_ID = "a69d6c98"           # 替换为你的 AppID
    ACCESS_KEY_ID = "XXX"        # 替换为你的 API Key
    ACCESS_KEY_SECRET = "XXX"   # 替换为你的 API Secret

    # 创建客户端
    client = RTASRClient(APP_ID, ACCESS_KEY_ID, ACCESS_KEY_SECRET)

    try:
        print("🎤 正在连接讯飞RTASR服务...")
        if not client.connect():
            print("❌ 连接失败，程序退出")
            exit(1)

        print("🎙️ 准备开始麦克风录音，按 Ctrl+C 停止...")

        # 启动实时录音和发送（最长60秒）
        client.start_microphone_streaming(max_duration=60)

        print("🔚 音频发送完成，等待识别结果...")

        # 继续监听几秒以便接收最后的结果
        time.sleep(8)

    except KeyboardInterrupt:
        print("\n🛑 用户中断，正在关闭...")
        client.stop()
        time.sleep(1)
    except Exception as e:
        print(f"【主流程异常】{str(e)}")
    finally:
        client.close()
        print("✅ 程序已退出")
