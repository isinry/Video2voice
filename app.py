import os
from flask import Flask, request, render_template, jsonify, send_file
from werkzeug.utils import secure_filename
import magic
from moviepy.editor import VideoFileClip
import tempfile
import speech_recognition as sr
from pydub import AudioSegment
import shutil
import threading
import queue
from concurrent.futures import ThreadPoolExecutor, TimeoutError

app = Flask(__name__)
# 增加文件大小限制到100MB
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
# 设置上传超时时间为300秒
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 300
# 设置请求超时时间为300秒
app.config['PERMANENT_SESSION_LIFETIME'] = 300

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 允许的视频文件类型
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_video_file(file_path):
    mime = magic.Magic(mime=True)
    file_type = mime.from_file(file_path)
    return file_type.startswith('video/')

def extract_audio(video_path, audio_path):
    video = VideoFileClip(video_path)
    video.audio.write_audiofile(audio_path)
    video.close()

def recognize_speech(audio_path):
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_path) as source:
        audio_data = recognizer.record(source)
        return recognizer.recognize_google(audio_data, language='zh-CN')

def convert_audio_to_text(audio_path):
    # 将音频转换为 WAV 格式（SpeechRecognition 需要）
    audio = AudioSegment.from_mp3(audio_path)
    wav_path = audio_path.replace('.mp3', '.wav')
    audio.export(wav_path, format='wav')
    
    try:
        # 使用线程池处理语音识别，设置超时时间为60秒
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(recognize_speech, wav_path)
            try:
                text = future.result(timeout=60)  # 60秒超时
                return text
            except TimeoutError:
                return "语音识别超时，请重试"
    except sr.UnknownValueError:
        return "无法识别音频内容"
    except sr.RequestError as e:
        return f"无法连接到语音识别服务；{str(e)}"
    finally:
        # 清理临时 WAV 文件
        if os.path.exists(wav_path):
            os.remove(wav_path)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': '没有文件被上传'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': '不支持的文件类型'}), 400

    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)

    if not is_video_file(file_path):
        os.remove(file_path)
        return jsonify({'error': '文件不是有效的视频文件'}), 400

    try:
        # 创建临时目录用于处理音频
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_audio_path = os.path.join(temp_dir, f"{os.path.splitext(filename)[0]}.mp3")
            
            # 使用线程池处理音频提取，设置超时时间为300秒
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(extract_audio, file_path, temp_audio_path)
                try:
                    future.result(timeout=300)  # 5分钟超时
                except TimeoutError:
                    return jsonify({'error': '处理文件超时，请尝试上传较小的文件'}), 500

            # 进行语音识别
            text = convert_audio_to_text(temp_audio_path)

            # 将音频文件复制到上传目录
            final_audio_path = os.path.join(app.config['UPLOAD_FOLDER'], os.path.basename(temp_audio_path))
            shutil.copy2(temp_audio_path, final_audio_path)

            # 发送音频文件和识别结果
            return jsonify({
                'audio_url': f'/download_audio/{os.path.basename(final_audio_path)}',
                'text': text
            })
    except Exception as e:
        return jsonify({'error': f'处理文件时出错: {str(e)}'}), 500
    finally:
        # 清理上传的视频文件
        if os.path.exists(file_path):
            os.remove(file_path)

@app.route('/download_audio/<filename>')
def download_audio(filename):
    audio_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(audio_path):
        return jsonify({'error': '音频文件不存在'}), 404
    
    try:
        return send_file(
            audio_path,
            mimetype='audio/mpeg',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({'error': f'下载文件时出错: {str(e)}'}), 500
    finally:
        # 下载完成后删除音频文件
        if os.path.exists(audio_path):
            os.remove(audio_path)

if __name__ == '__main__':
    app.run(debug=True) 