from flask import Flask, request, jsonify
import yt_dlp
import os

app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({
        "status": "online",
        "message": "yt-dlp JSON API for Pornhub is running",
        "proxy": "active"
    })

@app.route('/get_info')
def get_info():
    video_url = request.args.get('url')
    
    if not video_url:
        return jsonify({"error": "Missing 'url' parameter"}), 400

    proxy_url = "http://ytproxy-siawaseok.duckdns.org:3007"

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'proxy': proxy_url,
        'nocheckcertificate': True,
        'format': 'best',
        'referer': 'https://www.pornhub.com/',
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            return jsonify(info)
            
    except Exception as e:
        return jsonify({
            "error": "Failed to extract video information",
            "details": str(e)
        }), 500

@app.route('/api/v1/stream/<video_id>')
def get_stream_info(video_id):
    video_url = f"https://www.pornhub.com/view_video.php?viewkey={video_id}"
    proxy_url = "http://ytproxy-siawaseok.duckdns.org:3007"

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'proxy': proxy_url,
        'nocheckcertificate': True,
        'format': 'best',
        'referer': 'https://www.pornhub.com/',
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            
            return jsonify({
                "title": info.get("title"),
                "url": info.get("url"),
                "thumbnail": info.get("thumbnail"),
                "duration": info.get("duration"),
                "uploader": info.get("uploader")
            })
            
    except Exception as e:
        return jsonify({
            "error": "Failed to extract stream information",
            "details": str(e)
        }), 500

@app.route('/search')
def search_videos():
    query = request.args.get('q')
    if not query:
        return jsonify({"error": "Missing 'q' parameter"}), 400

    proxy_url = "http://ytproxy-siawaseok.duckdns.org:3007"
    
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'proxy': proxy_url,
        'nocheckcertificate': True,
        'extract_flat': False,
        'referer': 'https://www.pornhub.com/',
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        }
    }

    try:
        search_url = f"https://www.pornhub.com/video/search?search={query}"
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search_url, download=False)
            
            results = []
            if 'entries' in info:
                for entry in info['entries']:
                    results.append({
                        "title": entry.get("title"),
                        "url": entry.get("url") if entry.get("url") else (f"https://www.pornhub.com/view_video.php?viewkey={entry.get('id')}" if entry.get('id') else None),
                        "thumbnail": entry.get("thumbnail")
                    })
            
            return jsonify({
                "query": query,
                "results": results
            })
    except Exception as e:
        return jsonify({
            "error": "Failed to search videos",
            "details": str(e)
        }), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
