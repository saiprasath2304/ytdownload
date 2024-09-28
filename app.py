from flask import Flask, render_template, request, jsonify, send_file
import yt_dlp
import json
import requests
from io import BytesIO

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download_video():
    video_url = request.form.get('video_url')

    ydl_opts = {
        'format': 'best',
        'outtmpl': '%(title)s.%(ext)s',
        'noplaylist': True,
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }],
        'postprocessor_args': ['-crf', '23,'],
        'ratelimit': 1024 * 1024,
        'subtitleslangs': ['en'],
        'writesubtitles': True,
        'writethumbnail': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            output_json_path = 'static/video_info.json'
            with open(output_json_path, 'w', encoding='utf-8') as json_file:
                json.dump(info, json_file, ensure_ascii=False, indent=4)
            return jsonify({'success': True, 'info': info})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    
@app.route('/download-image')
def download_image():
    url = request.args.get('url')

    if not url:
        return "No URL provided", 400

    response = requests.get(url)

    if response.status_code == 200:
        return send_file(BytesIO(response.content), mimetype='image/jpeg', as_attachment=True, download_name='thumbnail.jpg')
    else:
        return "Error fetching the image", 500

@app.route('/downloadVnA')
def downVnA():
    video_url = request.args.get('vurl')
    audio_url = request.args.get('aurl')
    if not video_url:
        return jsonify({'success': False, 'error': 'No URL provided'}), 400

    output_file = 'videoplayback.mp4'
    ydl_opts = {
        'outtmpl': output_file,
        'format': 'best',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        
        return send_file(output_file, as_attachment=True)

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
