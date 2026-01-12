import webrtcvad
import wave
from pydub import AudioSegment


def read_wave(path):
    with wave.open(path, 'rb') as wf:
        sample_rate = wf.getframerate()
        frames = wf.readframes(wf.getnframes())
    return frames, sample_rate


def vad_detect(vad, frames, sample_rate):
    frame_duration = 20
    frame_size = int(sample_rate * frame_duration / 1000)
    is_speech = []

    for i in range(0, len(frames), frame_size):
        is_speech_frame = vad.is_speech(frames[i:i + frame_size], sample_rate)
        is_speech.append(is_speech_frame)

    return is_speech


def voice_split(audio, speech_flags):
    silent_time = 25
    valid_length = 50
    n = len(speech_flags)
    valid_segments = []
    start = 0  # 当前段的起始位置
    current_false = 0  # 当前连续False计数

    for i in range(n):
        if not speech_flags[i]:  # 当前是False
            current_false += 1
            if current_false > silent_time:  # 发现超过25个连续False
                # 计算有效结束位置（当前False序列的起始前一位）
                end = i - current_false
                # 如果段长度足够则记录
                if end >= start and (end - start + 1) >= valid_length:
                    valid_segments.append((start, end))
                # 重置起始点为当前False序列的下一个位置
                start = i + 1
                current_false = 0
        else:  # 当前是True
            current_false = 0

    # 处理最后未结束的段
    if n - start >= 50:
        valid_segments.append((start, n - 1))

    return valid_segments


# 主程序入口
def main():
    vad = webrtcvad.Vad()
    vad.set_mode(1)  # 设置VAD的模式
    audio, sample_rate = read_wave('read_book.wav')  # 读取音频文件
    # print(str(audio) + "+" + str(sample_rate))
    speech_flags = vad_detect(vad, audio, sample_rate)  # 运行VAD检测

    # 处理结果
    for flag in speech_flags:
        print('1' if flag else '0', end='')
    valid_segments = voice_split(audio, speech_flags)
    print('total segments: ' + str(len(valid_segments)))
    for i in valid_segments:
        print('start: ' + str(i[0]) + ' ' + 'end:' + str(i[1]) + '       ', end='')


if __name__ == "__main__":
    main()
