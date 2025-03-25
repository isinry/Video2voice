# 视频声音提取器

这是一个简单的Web应用，可以从视频文件中提取音频。支持多种视频格式，包括MP4、AVI、MOV、MKV、WMV和FLV。

## 功能特点

- 支持文件拖拽上传
- 支持文件选择上传
- 自动验证文件类型
- 文件大小限制（16MB）
- 美观的用户界面
- 实时错误提示
- 自动下载提取的音频文件

## 安装要求

- Python 3.6+
- FFmpeg（用于音频处理）

## 安装步骤

1. 克隆或下载此仓库
2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
3. 安装FFmpeg（如果尚未安装）：
   - macOS: `brew install ffmpeg`
   - Ubuntu: `sudo apt-get install ffmpeg`
   - Windows: 从 [FFmpeg官网](https://ffmpeg.org/download.html) 下载并添加到系统PATH

## 运行应用

```bash
python app.py
```

然后在浏览器中访问 `http://localhost:5000`

## 使用说明

1. 打开网页后，你可以：
   - 将视频文件拖放到虚线框内
   - 点击"选择文件"按钮选择视频文件
2. 系统会自动验证文件类型和大小
3. 上传成功后，系统会自动处理并下载提取的音频文件（MP3格式）

## 注意事项

- 确保上传的视频文件大小不超过16MB
- 支持的文件格式：MP4、AVI、MOV、MKV、WMV、FLV
- 处理大文件可能需要一些时间，请耐心等待 


## 待开发功能 [TODOLIST](./TODOLIST.md)