import base64
import json
import os
import datetime
from typing import Optional, List, Dict, Tuple, Any

from tencentcloud.common import credential
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.asr.v20190614 import asr_client, models


class TencentVoicePrintClient:
    """
    腾讯云说话人识别接口完整封装类
    包含：注册、认证、更新、删除、比对、统计、1:N验证 所有接口
    """

    def __init__(self, secret_id: str, secret_key: str, region: str = "ap-guangzhou", save_path: str = "speaker_info.json"):
        """
        初始化客户端
        :param secret_id: 腾讯云SecretId
        :param secret_key: 腾讯云SecretKey
        :param region: 地域（默认ap-guangzhou）
        :param save_path: 说话人信息本地保存路径
        """
        self.secret_id = secret_id
        self.secret_key = secret_key
        self.region = region
        self.save_path = save_path
        self.client = self._init_client()

    def _init_client(self) -> asr_client.AsrClient:
        """初始化腾讯云ASR客户端"""
        try:
            # 初始化认证信息
            cred = credential.Credential(self.secret_id, self.secret_key)

            # 配置HTTP参数
            http_profile = HttpProfile()
            http_profile.endpoint = "asr.tencentcloudapi.com"
            http_profile.reqTimeout = 30  # 超时时间30秒
            http_profile.region = self.region

            # 配置客户端
            client_profile = ClientProfile()
            client_profile.httpProfile = http_profile

            # 创建客户端实例
            client = asr_client.AsrClient(cred, self.region, client_profile)
            return client
        except TencentCloudSDKException as e:
            raise Exception(f"客户端初始化失败: {e}")

    def _audio_to_base64(self, audio_path: str) -> str:
        """
        音频文件转base64编码
        :param audio_path: 音频文件路径（PCM/WAV，16k/16bit/单声道）
        :return: base64编码字符串
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"音频文件不存在: {audio_path}")

        try:
            with open(audio_path, "rb") as f:
                audio_data = f.read()
            # 校验音频大小（不超过2M）
            if len(audio_data) > 2 * 1024 * 1024:
                raise ValueError("音频文件大小超过2M限制")
            return base64.b64encode(audio_data).decode("utf-8")
        except Exception as e:
            raise Exception(f"音频转base64失败: {e}")

    def _save_speaker_info(self, voice_print_id: str, speaker_nick: str, group_id: str = "default_group") -> None:
        """
        本地保存说话人信息（自动调用，无需手动调用）
        :param voice_print_id: 说话人唯一ID
        :param speaker_nick: 说话人昵称
        :param group_id: 分组ID
        """
        # 读取已有数据
        if os.path.exists(self.save_path):
            with open(self.save_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = {}

        # 更新数据
        data[voice_print_id] = {
            "speaker_nick": speaker_nick,
            "group_id": group_id,
            "create_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "update_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        # 保存数据
        with open(self.save_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def _update_speaker_info(self, voice_print_id: str, speaker_nick: Optional[str] = None) -> None:
        """更新本地保存的说话人信息"""
        if not os.path.exists(self.save_path):
            return

        with open(self.save_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if voice_print_id in data:
            if speaker_nick:
                data[voice_print_id]["speaker_nick"] = speaker_nick
            data[voice_print_id]["update_time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            with open(self.save_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

    def _delete_speaker_info(self, voice_print_id: str) -> None:
        """删除本地保存的说话人信息"""
        if not os.path.exists(self.save_path):
            return

        with open(self.save_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if voice_print_id in data:
            del data[voice_print_id]
            with open(self.save_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

    # -------------------------- 核心接口封装 --------------------------
    def enroll_speaker(self, audio_path: str, speaker_nick: str, voice_format: int = 1,
                       sample_rate: int = 16000, group_id: str = "default_group") -> Dict[str, Any]:
        """
        说话人注册
        :param audio_path: 注册音频文件路径
        :param speaker_nick: 说话人昵称（≤32字节）
        :param voice_format: 音频格式 0=PCM, 1=WAV
        :param sample_rate: 采样率（固定16000）
        :param group_id: 分组ID（仅支持字母、数字、下划线，≤128字符）
        :return: 注册结果字典
        """
        try:
            req = models.VoicePrintEnrollRequest()
            req.VoiceFormat = voice_format
            req.SampleRate = sample_rate
            req.Data = self._audio_to_base64(audio_path)
            req.SpeakerNick = speaker_nick
            req.GroupId = group_id

            # 调用接口
            resp = self.client.VoicePrintEnroll(req)

            # 解析结果
            result = {
                "voice_print_id": resp.Data.VoicePrintId,
                "speaker_nick": resp.Data.SpeakerNick,
                "request_id": resp.RequestId
            }

            # 保存到本地
            self._save_speaker_info(result["voice_print_id"], speaker_nick, group_id)

            print(f"✅ 说话人注册成功\n"
                  f"说话人昵称: {speaker_nick}\n"
                  f"VoicePrintId: {result['voice_print_id']}\n"
                  f"分组ID: {group_id}")
            return result

        except TencentCloudSDKException as e:
            raise Exception(f"说话人注册失败: {e}")

    def verify_speaker(self, audio_path: str, voice_print_id: str, voice_format: int = 1,
                       sample_rate: int = 16000) -> Dict[str, Any]:
        """
        说话人认证（1:1验证）
        :param audio_path: 待验证音频文件路径
        :param voice_print_id: 已注册的说话人ID
        :param voice_format: 音频格式 0=PCM, 1=WAV
        :param sample_rate: 采样率（固定16000）
        :return: 验证结果字典（包含相似度分数、是否匹配）
        """
        try:
            req = models.VoicePrintVerifyRequest()
            req.VoiceFormat = voice_format
            req.SampleRate = sample_rate
            req.Data = self._audio_to_base64(audio_path)
            req.VoicePrintId = voice_print_id

            # 调用接口
            resp = self.client.VoicePrintVerify(req)

            # 解析结果
            score = float(resp.Data.Score)
            decision = resp.Data.Decision  # 1=匹配，0=不匹配
            result = {
                "voice_print_id": resp.Data.VoicePrintId,
                "score": score,
                "decision": decision,
                "is_match": decision == 1,
                "request_id": resp.RequestId
            }

            print(f"✅ 说话人认证完成\n"
                  f"VoicePrintId: {voice_print_id}\n"
                  f"相似度分数: {score}\n"
                  f"是否匹配: {'是' if result['is_match'] else '否'}")
            return result

        except TencentCloudSDKException as e:
            raise Exception(f"说话人认证失败: {e}")

    def update_speaker(self, audio_path: str, voice_print_id: str, speaker_nick: Optional[str] = None,
                       voice_format: int = 1, sample_rate: int = 16000) -> Dict[str, Any]:
        """
        说话人更新（覆盖音频和昵称）
        :param audio_path: 新的音频文件路径
        :param voice_print_id: 已注册的说话人ID
        :param speaker_nick: 新的说话人昵称（可选）
        :param voice_format: 音频格式 0=PCM, 1=WAV
        :param sample_rate: 采样率（固定16000）
        :return: 更新结果字典
        """
        try:
            req = models.VoicePrintUpdateRequest()
            req.VoiceFormat = voice_format
            req.SampleRate = sample_rate
            req.Data = self._audio_to_base64(audio_path)
            req.VoicePrintId = voice_print_id
            if speaker_nick:
                req.SpeakerNick = speaker_nick

            # 调用接口
            resp = self.client.VoicePrintUpdate(req)

            # 解析结果
            result = {
                "voice_print_id": resp.Data.VoicePrintId,
                "speaker_nick": resp.Data.SpeakerNick,
                "request_id": resp.RequestId
            }

            # 更新本地信息
            self._update_speaker_info(voice_print_id, speaker_nick)

            print(f"✅ 说话人信息更新成功\n"
                  f"VoicePrintId: {voice_print_id}\n"
                  f"新昵称: {speaker_nick or '未修改'}")
            return result

        except TencentCloudSDKException as e:
            raise Exception(f"说话人更新失败: {e}")

    def delete_speaker(self, voice_print_id: str, del_mod: int = 0) -> Dict[str, Any]:
        """
        说话人删除
        :param voice_print_id: 说话人ID
        :param del_mod: 删除模式 0=删除声纹 1=从分组移除 2=删除分组
        :return: 删除结果字典
        """
        try:
            req = models.VoicePrintDeleteRequest()
            req.VoicePrintId = voice_print_id
            req.DelMod = del_mod

            # 调用接口
            resp = self.client.VoicePrintDelete(req)

            # 解析结果
            result = {
                "voice_print_id": resp.Data.VoicePrintId,
                "speaker_nick": resp.Data.SpeakerNick,
                "request_id": resp.RequestId
            }

            # 删除本地信息（仅当del_mod=0时删除）
            if del_mod == 0:
                self._delete_speaker_info(voice_print_id)

            print(f"✅ 说话人删除成功\n"
                  f"VoicePrintId: {voice_print_id}\n"
                  f"删除模式: {del_mod}")
            return result

        except TencentCloudSDKException as e:
            raise Exception(f"说话人删除失败: {e}")

    def compare_voices(self, src_audio_path: str, dest_audio_path: str, voice_format: int = 1,
                       sample_rate: int = 16000) -> Dict[str, Any]:
        """
        说话人比对（两段音频直接比对）
        :param src_audio_path: 源音频路径
        :param dest_audio_path: 目标音频路径
        :param voice_format: 音频格式 0=PCM, 1=WAV
        :param sample_rate: 采样率（固定16000）
        :return: 比对结果字典
        """
        try:
            req = models.VoicePrintCompareRequest()
            req.VoiceFormat = voice_format
            req.SampleRate = sample_rate
            req.SrcAudioData = self._audio_to_base64(src_audio_path)
            req.DestAudioData = self._audio_to_base64(dest_audio_path)

            # 调用接口
            resp = self.client.VoicePrintCompare(req)

            # 解析结果
            score = float(resp.Data.Score)
            decision = resp.Data.Decision
            result = {
                "score": score,
                "decision": decision,
                "is_match": decision == 1,
                "request_id": resp.RequestId
            }

            print(f"✅ 音频比对完成\n"
                  f"相似度分数: {score}\n"
                  f"是否为同一人: {'是' if result['is_match'] else '否'}")
            return result

        except TencentCloudSDKException as e:
            raise Exception(f"音频比对失败: {e}")

    def count_speakers(self, group_id: str = "", count_mod: int = 0) -> Dict[str, Any]:
        """
        说话人注册数量统计
        :param group_id: 分组ID（count_mod=1时必填）
        :param count_mod: 统计模式 0=统计所有 1=统计指定分组
        :return: 统计结果字典
        """
        try:
            req = models.VoicePrintCountRequest()
            req.GroupId = group_id
            req.CountMod = count_mod

            # 调用接口
            resp = self.client.VoicePrintCount(req)

            # 解析结果
            result = {
                "total": resp.Data.Total,
                "request_id": resp.RequestId
            }

            print(f"✅ 说话人数量统计完成\n"
                  f"统计模式: {count_mod}\n"
                  f"分组ID: {group_id or '所有分组'}\n"
                  f"总数: {result['total']}")
            return result

        except TencentCloudSDKException as e:
            raise Exception(f"统计失败: {e}")

    def group_verify_speaker(self, audio_path: str, group_id: str, top_n: int = 1,
                             voice_format: int = 1, sample_rate: int = 16000) -> Dict[str, Any]:
        """
        说话人验证1:N
        :param audio_path: 待验证音频路径
        :param group_id: 分组ID
        :param top_n: 返回TopN结果（>0且<最大注册数）
        :param voice_format: 音频格式 0=PCM, 1=WAV
        :param sample_rate: 采样率（固定16000）
        :return: 1:N验证结果字典
        """
        try:
            req = models.VoicePrintGroupVerifyRequest()
            req.VoiceFormat = voice_format
            req.SampleRate = sample_rate
            req.Data = self._audio_to_base64(audio_path)
            req.GroupId = group_id
            req.TopN = top_n

            # 调用接口
            resp = self.client.VoicePrintGroupVerify(req)

            # 解析结果
            verify_tops = []
            for item in resp.Data.VerifyTops:
                verify_tops.append({
                    "voice_print_id": item.VoicePrintId,
                    "speaker_nick": item.SpeakerId,
                    "score": float(item.Score)
                })

            result = {
                "verify_tops": verify_tops,
                "request_id": resp.RequestId
            }

            # 打印结果
            print(f"✅ 1:N验证完成（Top{top_n}）")
            for i, item in enumerate(verify_tops, 1):
                print(f"{i}. 说话人: {item['speaker_nick']} | 相似度: {item['score']} | ID: {item['voice_print_id']}")

            return result

        except TencentCloudSDKException as e:
            raise Exception(f"1:N验证失败: {e}")

    # -------------------------- 辅助查询接口 --------------------------
    def query_speaker_info(self, condition: str) -> List[Dict[str, Any]]:
        """
        查询本地保存的说话人信息
        :param condition: 查询条件（VoicePrintId/昵称/分组ID）
        :return: 匹配的说话人信息列表
        """
        if not os.path.exists(self.save_path):
            print("暂无本地保存的说话人信息")
            return []

        with open(self.save_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        results = []
        for voice_print_id, info in data.items():
            if (condition == voice_print_id) or (condition == info["speaker_nick"]) or (condition == info["group_id"]):
                results.append({
                    "voice_print_id": voice_print_id,
                    "speaker_nick": info["speaker_nick"],
                    "group_id": info["group_id"],
                    "create_time": info["create_time"],
                    "update_time": info["update_time"]
                })

        if results:
            print(f"✅ 查询到 {len(results)} 条匹配的说话人信息")
            for i, res in enumerate(results, 1):
                print(f"{i}. {res}")
        else:
            print(f"❌ 未查询到匹配 '{condition}' 的说话人信息")

        return results