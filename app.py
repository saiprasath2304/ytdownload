from flask import Flask, render_template, request, jsonify, send_file
import yt_dlp
import json
import requests
from io import BytesIO
import os

app = Flask(__name__)

# Replace with your YouTube Data API v3 key
API_KEY = os.getenv('YOUTUBE_API_KEY', 'YOUR_API_KEY')  # Replace with your actual API key

def fetch_from_api(url, params):
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API Error: {e}")
        return None

def get_video_info(video_id):
    """Fetch video metadata using YouTube Data API v3"""
    url = f'https://www.googleapis.com/youtube/v3/videos?id={video_id}&key={API_KEY}&part=snippet,statistics'
    response = requests.get(url)
    video_info = response.json()

    if 'items' in video_info:
        return video_info['items'][0]  # Return the video metadata
    else:
        return None
    
def get_video_analytics(video_id):
    """Fetch video analytics data using YouTube Analytics API v2."""
    
    # YouTube Analytics API URL
    analytics_url = 'https://youtubeanalytics.googleapis.com/v2/reports'
    
    # Parameters for fetching analytics data (impressions, views, etc.)
    params = {
        'ids': f'video=={video_id}',
        'startDate': '2024-01-01',  # Replace with your desired start date
        'endDate': '2024-01-29',    # Replace with your desired end date
        'metrics': 'impressions,views,averageWatchTime,estimatedMinutesWatched',
        'dimensions': 'video',
        'key': API_KEY  # API Key for authentication
    }

    # Making the API request to YouTube Analytics
    response = requests.get(analytics_url, params=params)
    print("response", response)
    analytics_data = response.json()
    print(analytics_data)

    # If the API call returns 'rows', extract the analytics data
    if 'rows' in analytics_data:
        # The analytics data is returned in rows; extract the first row's data
        analytics = analytics_data['rows'][0]
        
        # Return the analytics data in a structured format
        return {
            'impressions': analytics[0],  # Impressions
            'views': analytics[1],        # Views
            'average_watch_time': analytics[2],  # Average watch time
            'estimated_minutes_watched': analytics[3]  # Estimated minutes watched
        }
    else:
        return {'error': 'No analytics data found or invalid video ID'}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video')
def video():
    return render_template('video.html')

@app.route('/download', methods=['POST'])
def download_video():
    video_url = request.form.get('video_url')
    # print(video_url)
    if(video_url.__contains__("youtu.be")):
        video_id = video_url.split("/")[3].split("?")[0]
    elif(video_url.__contains__("shorts")):
        video_id = video_url.split("/")[4].split("?")[0]
    else:
        video_id = video_url.split("v=")[1]
    # print(video_id)

    # Fetch video metadata
    video_info = get_video_info(video_id)

    if video_info:
        # Check if there are any restrictions (e.g., age-restricted)
        restrictions = video_info.get('status', {}).get('restrictions', [])
        
        if restrictions:
            return jsonify({'success': False, 'error': 'Video is restricted. Please login or bypass restrictions.'})
        
        # Video is not restricted, proceed with downloading
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': '%(title)s.%(ext)s',
            'noplaylist': True,
            'cookiefile': 'cookies.txt',
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
            'postprocessor_args': ['-crf', '23'],
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
    else:
        return jsonify({'success': False, 'error': 'Video not found or invalid video ID.'})
    
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
    
def get_channel_info(channel_id=None, for_username=None):
    """
    Fetch channel metadata using YouTube Data API v3.
    You can use either `channel_id` or `for_username`.
    """
    if not channel_id and not for_username:
        return None

    base_url = 'https://www.googleapis.com/youtube/v3/channels'
    params = {
        'key': API_KEY,
        'part': 'snippet,contentDetails,statistics',  # Include statistics part for view and subscriber count
    }
    if channel_id:
        params['id'] = channel_id
    elif for_username:
        params['forUsername'] = for_username

    response = requests.get(base_url, params=params)
    channel_info = response.json()

    if 'items' in channel_info and len(channel_info['items']) > 0:
        return channel_info
    else:
        return None
    
def get_videos_from_playlist(playlist_id):
    """
    Fetch all videos from the given playlist ID.
    """
    base_url = 'https://www.googleapis.com/youtube/v3/playlistItems'
    params = {
        'key': API_KEY,
        'part': 'snippet,contentDetails',
        'playlistId': playlist_id,
        'maxResults': 50  # Fetch 50 items per page
    }
    videos = []
    while True:
        response = requests.get(base_url, params=params).json()
        videos.extend(response.get('items', []))
        next_page_token = response.get('nextPageToken')
        if not next_page_token:
            break
        params['pageToken'] = next_page_token
    return videos


def get_playlists_by_channel(channel_id):
    """
    Fetch all playlists created by the channel.
    """
    base_url = 'https://www.googleapis.com/youtube/v3/playlists'
    params = {
        'key': API_KEY,
        'part': 'snippet,contentDetails',
        'channelId': channel_id,
        'maxResults': 50
    }
    playlists = []
    while True:
        response = requests.get(base_url, params=params).json()
        playlists.extend(response.get('items', []))
        next_page_token = response.get('nextPageToken')
        if not next_page_token:
            break
        params['pageToken'] = next_page_token
    return playlists

    
@app.route('/channel-info', methods=['GET'])
def channel_info():
    channel_id = request.args.get('channel_id')
    username = request.args.get('username')

    if not channel_id and not username:
        return jsonify({'success': False, 'error': 'Provide a channel_id or username'}), 400

    # Fetch basic channel info
    channel_data = get_channel_info(channel_id=channel_id, for_username=username)
    if not channel_data:
        return jsonify({'success': False, 'error': 'Channel not found or invalid input'}), 404

    # Fetching statistics like viewCount and subscriberCount
    statistics = channel_data['items'][0].get('statistics', {})
    view_count = statistics.get('viewCount', 'N/A')
    subscriber_count = statistics.get('subscriberCount', 'N/A')
    video_count = statistics.get('videoCount', 'N/A')
    hidden_subscriber_count = statistics.get('hiddenSubscriberCount', 'N/A')

    return jsonify({
        'success': True,
        'statistics': statistics,
        'channel_data': channel_data,
        'channel_info': {
            'view_count': view_count,
            'subscriber_count': subscriber_count,
            'video_count': video_count,
            'hidden_subscriber_count': hidden_subscriber_count
        }
    })

@app.route('/video-info', methods=['GET'])
def video_info():
    video_id = request.args.get('video_id')

    if not video_id:
        return jsonify({'success': False, 'error': 'Provide a video_id'}), 400

    # Fetch video data including viewCount, likeCount, etc.
    video_data = get_video_info(video_id)
    if not video_data:
        return jsonify({'success': False, 'error': 'Video not found or invalid ID'}), 404

    statistics = video_data.get('statistics', {})
    view_count = statistics.get('viewCount', 'N/A')
    like_count = statistics.get('likeCount', 'N/A')
    dislike_count = statistics.get('dislikeCount', 'N/A')  # Note: this might be restricted for some videos
    comment_count = statistics.get('commentCount', 'N/A')

    return jsonify({
        'success': True,
        'statistics': statistics,
        'video_data': video_data,
        'video_info': {
            'view_count': view_count,
            'like_count': like_count,
            'dislike_count': dislike_count,
            'comment_count': comment_count
        }
    })

@app.route('/analytics-info', methods=['GET'])
def analytics_info():
    an_id = request.args.get('video_id')

    if not an_id:
        return jsonify({'success': False, 'error': 'Provide a video_id'}), 400

    # Fetch video data including viewCount, likeCount, etc.
    video_data = get_video_analytics(an_id)
    if not video_data:
        return jsonify({'success': False, 'error': 'Video not found or invalid ID'}), 404
    
    return jsonify({
        'success': True,
        'video_data': video_data
    })

if __name__ == '__main__':
    app.run(debug=True)
