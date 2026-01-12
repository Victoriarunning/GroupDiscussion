import sounddevice as sd
from scipy.io.wavfile import write


def record_audio(filename="output.wav", duration=5, sample_rate=16000):
    """
    使用麦克风录制音频并保存为wav文件
    :param filename: 保存的文件名
    :param duration: 录音时长，单位秒
    :param sample_rate: 采样率，默认为44100Hz
    """
    print("开始录音...")
    audio_data = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
    sd.wait()  # 等待录音完成
    print("录音完成！保存文件中...")

    write(filename, sample_rate, audio_data)
    print(f"音频已保存为 {filename}")


# 调用录音函数
if __name__ == '__main__':
    record_audio("huangpu.wav", duration=5)
