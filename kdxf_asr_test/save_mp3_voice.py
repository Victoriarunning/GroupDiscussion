import sounddevice as sd
from scipy.io.wavfile import write
from pydub import AudioSegment
import os


def record_audio_to_mp3(filename, duration=10, fs=16000):
    """
    录音并保存为MP3文件

    参数:
        filename: 输出文件名(不带扩展名)
        duration: 录音时长(秒)
        fs: 采样率(Hz)
    """
    # 录音
    print(f"开始录音，时长{duration}秒...")
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()  # 等待录音完成
    print("录音完成")

    # 临时保存为WAV文件
    temp_wav = f"{filename}_temp.wav"
    write(temp_wav, fs, recording)

    # 转换为MP3
    print("正在转换为MP3...")
    sound = AudioSegment.from_wav(temp_wav)
    sound.export(f"{filename}.mp3", format="mp3", bitrate="16k")

    # 删除临时WAV文件
    os.remove(temp_wav)
    print(f"文件已保存为 {filename}.mp3")


# 使用示例
if __name__ == '__main__':
    record_audio_to_mp3("target", duration=3)
