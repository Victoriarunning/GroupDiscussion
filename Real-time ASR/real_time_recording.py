import threading
import time
import wave
import pyaudio
from datetime import datetime
from recording_segment import segment_process


class AudioRecorder:
    def __init__(self):
        self.CHUNK = 1024  # 每次读取的音频数据块大小
        self.FORMAT = pyaudio.paInt16  # 音频格式
        self.CHANNELS = 1  # 单声道
        self.RATE = 16000  # 采样率
        self.RECORD_SECONDS = 5  # 每次录音时长
        self.is_recording = False
        self.audio = pyaudio.PyAudio()
        self.frames = []

    def start_recording(self):
        self.is_recording = True
        self.stream = self.audio.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK
        )
        print("Recording started...")

        # 启动新线程处理录音
        threading.Thread(target=self.record).start()

    def stop_recording(self):
        self.is_recording = False
        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()
        print("Recording stopped.")

    def record(self):
        while self.is_recording:
            start_time = time.time()
            self.frames = []  # 清空帧列表

            # 录制5秒音频
            for _ in range(0, int(self.RATE / self.CHUNK * self.RECORD_SECONDS)):
                if not self.is_recording:
                    break
                data = self.stream.read(self.CHUNK)
                self.frames.append(data)

            # 保存为WAV文件
            if self.frames:
                self.save_to_wav()

    def save_to_wav(self):
        # 生成带时间戳的文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        times = datetime.now().strftime("%H:%M:%S")
        filename = f"recording_{timestamp}.wav"
        filepath = f"Recording/" + filename
        wf = wave.open(filepath, 'wb')
        wf.setnchannels(self.CHANNELS)
        wf.setsampwidth(self.audio.get_sample_size(self.FORMAT))
        wf.setframerate(self.RATE)
        wf.writeframes(b''.join(self.frames))
        wf.close()
        print(f"Recorder is saving recording to {filename}")
        segment_process(filepath, "segment_recording", times)


if __name__ == "__main__":
    recorder = AudioRecorder()

    try:
        recorder.start_recording()
        # 主线程可以继续做其他事情
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        recorder.stop_recording()
