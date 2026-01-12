import wave
import base64


# def read_wav_file(file_path):
#     with wave.open(file_path, 'rb') as wav_file:
#         num_frames = wav_file.getnframes()
#         frame_width = wav_file.getsampwidth()
#         frames = wav_file.readframes(num_frames)
#     return frames, frame_width
#
#
# def wav_to_base64(file_path):
#     frames, frame_width = read_wav_file(file_path)
#     base64_encoded = base64.b64encode(frames).decode('utf-8')
#     return base64_encoded


def main():
    file_path = 'my_recording3.wav'  # 替换为你的WAV文件路径
    with open(file_path, "rb") as f:
        base64_data = base64.b64encode(f.read()).decode()
    # print(base64_data)
    return base64_data


if __name__ == "__main__":
    main()
