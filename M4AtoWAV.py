from pydub import AudioSegment

# 加载M4A文件
audio = AudioSegment.from_file("FirstGroup_FirstDiscussion.m4a", format="m4a")

# 将音频文件保存为WAV格式
audio.export("discussion1.m4a", format="wav")

print("转换完成！")
