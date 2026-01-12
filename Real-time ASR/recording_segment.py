import os
import shutil
import struct
from collections import deque
import webrtcvad
from pydub import AudioSegment
import wave
from datetime import datetime
import threading
from speech_recognition import speech_recognition
from speaker_recognition import req_url
from statement_manager import statement_manager


def recognition(file_path, times):
    text = speech_recognition(file_path)
    if text == '':
        print('there is no voice')
        return
    speaker, score = req_url('search feature', group_id='home', file_path=file_path)
    print('====*Recognition*====', times, ':', speaker, ':', text)
    statement_manager.add_statements(times + '&' + speaker + '&' + text)



def split_audio_with_vad(input_file, output_dir, times, aggressiveness=3,
                         min_activity_duration=1.0, max_silence_duration=0.3,
                         frame_duration_ms=30, sample_rate=16000):
    """
    使用VAD分割音频文件，并确保结尾的活动音频被单独保存

    参数:
        input_file: 输入音频文件路径
        output_dir: 输出目录路径
        aggressiveness: VAD攻击性(0-3)，越高越严格
        min_activity_duration: 最小语音活动时长(秒)
        max_silence_duration: 最大允许连续静音时长(秒)
        frame_duration_ms: VAD分析帧时长(毫秒)
        sample_rate: 目标采样率(Hz)
    """
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)

    # 加载音频文件并转换为单声道16kHz
    audio = AudioSegment.from_file(input_file)
    audio = audio.set_frame_rate(sample_rate).set_channels(1)

    # 初始化VAD
    vad = webrtcvad.Vad(aggressiveness)

    # 将音频转换为原始PCM数据
    raw_data = audio.raw_data
    sample_width = audio.sample_width
    frame_size = int(sample_rate * frame_duration_ms / 1000 * sample_width)

    # 分割音频为帧
    frames = [
        raw_data[i * frame_size: (i + 1) * frame_size]
        for i in range(len(raw_data) // frame_size)
    ]

    # 检测每帧是否为语音
    voiced_frames = []
    for frame in frames:
        if len(frame) < frame_size:
            continue  # 跳过不完整的帧
        is_speech = vad.is_speech(frame, sample_rate)
        voiced_frames.append(is_speech)

    for frame in voiced_frames:
        if frame:
            print('1', end='')
        else:
            print('0', end='')

    # 转换为时间序列(秒)
    frame_times = [i * frame_duration_ms / 1000 for i in range(len(voiced_frames))]

    # 分割逻辑
    segments = []
    current_segment_start = 0
    last_voice_time = 0
    max_silence_frames = int(max_silence_duration * 1000 / frame_duration_ms)

    silence_buffer = deque(maxlen=max_silence_frames)
    has_activity = False

    for i, (time, is_voice) in enumerate(zip(frame_times, voiced_frames)):
        silence_buffer.append(is_voice)

        if is_voice:
            last_voice_time = time
            has_activity = True

        # 检查是否超过最大静音时长
        if not any(silence_buffer):
            if has_activity:
                # 检查是否满足最小活动时长
                active_duration = last_voice_time - frame_times[current_segment_start]
                if active_duration >= min_activity_duration:
                    segments.append((frame_times[current_segment_start], time))
                current_segment_start = i + 1
                has_activity = False
            else:
                current_segment_start = i + 1
    # 特殊处理最后一个片段（即使没有检测到静音结尾）
    if has_activity:
        # 确保不会超过音频总长度
        end_time = min(frame_times[-1] + frame_duration_ms / 1000, len(audio) / 1000)
        segments.append((frame_times[current_segment_start], end_time))

    # 导出分割后的音频
    # base_name = os.path.splitext(os.path.basename(input_file))[0]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    for i, (start, end) in enumerate(segments):
        start_ms = int(start * 1000)
        end_ms = int(end * 1000)
        segment = audio[start_ms:end_ms]

        # 如果是最后一个片段且包含活动语音，使用特殊命名
        if i == len(segments) - 1 and has_activity:
            output_path = os.path.join(output_dir, f"the_final_active_segment.wav")
            segment.export(output_path, format="wav")
        else:
            output_path = os.path.join(output_dir, f"{timestamp}_segment_{i + 1}.wav")
            segment.export(output_path, format="wav")
            # 识别分割后的语音片段
            thread = threading.Thread(target=recognition, args=(output_path, time_add(times, start)))
            # recognition(output_path, time_add(times, start))
            thread.start()

    return len(segments)


def time_add(time, add):
    split_time = time.split(':')
    hour = int(split_time[0])
    minute = int(split_time[1])
    second = int(split_time[2])
    if second + add >= 60:
        second = int(second + add - 60)
        if minute + 1 == 60:
            minute = 0
            hour += 1
        else:
            minute += 1
    else:
        second = int(second + add)
    return '' + str(hour) + ':' + str(minute) + ':' + str(second)


def segment_process(input_file, output_dir, times):
    current_file = merge_or_return_wav(output_dir + "/the_final_active_segment.wav", input_file,
                                       output_dir + "/target_file.wav")
    num_segments = split_audio_with_vad(current_file, output_dir, times)
    print(f"分割完成，共生成{num_segments}个片段")


def merge_or_return_wav(remain_file, current_file, output_file):
    """
    合并两个.wav文件，但如果第一个文件不存在，则直接返回第二个文件

    :param remain_file: 上个文件遗留的.wav文件路径
    :param current_file: 现处理的.wav文件路径
    :param output_file: 合并后的输出文件路径
    :return: True表示操作成功，False表示失败
    """
    # 检查遗留文件是否存在
    if not os.path.exists(remain_file):
        print(f"提示：文件 '{remain_file}' 不存在，直接返回 '{output_file}'")
        try:
            shutil.copy2(current_file, output_file)  # 直接复制第二个文件到输出文件
            print(f"已复制 '{current_file}' 到 '{output_file}'")
            return output_file
        except Exception as e:
            print(f"复制文件失败: {str(e)}")
            return False

    # 检查现处理文件是否存在
    if not os.path.exists(current_file):
        print(f"错误：文件 '{current_file}' 不存在！")
        return False

    try:
        # 打开遗留.wav文件
        with wave.open(remain_file, 'rb') as wav1:
            params1 = wav1.getparams()
            data1 = wav1.readframes(wav1.getnframes())

        # 打开现处理.wav文件
        with wave.open(current_file, 'rb') as wav2:
            params2 = wav2.getparams()
            data2 = wav2.readframes(wav2.getnframes())

            # 检查两个文件的参数是否相同（采样率、采样宽度、声道数等）
            if params1[0] != params2[0] or params1[1] != params2[1] or params1[2] != params2[2]:
                print("错误：两个.wav文件的参数不匹配（采样率、采样宽度或声道数不同），无法合并！")
                return False

            # 合并音频数据
            merged_data = data1 + data2

            # 写入合并后的文件
            with wave.open(output_file, 'wb') as merged:
                merged.setparams(params1)
                merged.writeframes(merged_data)
        os.remove(remain_file)
        print(f"成功合并 '{remain_file}' 和 '{current_file}' 到 '{output_file}' ，并移除 '{remain_file}'")
        return output_file

    except Exception as e:
        print(f"合并过程中发生错误: {str(e)}")
        return False


# 使用示例
# if __name__ == "__main__":
#     input_file = "read_book.wav"  # 替换为你的音频文件
#     output_dir = "segment_recording"
#     num_segments = split_audio_with_vad(input_file, output_dir)
#     print(f"分割完成，共生成{num_segments}个片段")
