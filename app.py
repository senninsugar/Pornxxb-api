from flask import Flask, request, Response, jsonify
import yt_dlp
import requests
import os

app = Flask(__name__)

# 指定されたプロキシ
PROXY_URL = "http://ytproxy-siawaseok.duckdns.org:3007"
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'

@app.route('/get_info')
def get_info():
    video_url = request.args.get('url')
    if not video_url:
        return jsonify({"error": "Missing url"}), 400

    ydl_opts = {
        'quiet': True,
        'proxy': PROXY_URL,
        'user_agent': USER_AGENT,
        'referer': 'https://www.pornhub.com/',
        'nocheckcertificate': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            # JSON内のストリームURLを、このサーバー経由のプロキシURLに書き換える（簡易版）
            return jsonify(info)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 動画データそのものをプロキシ経由で中継する
@app.route('/proxy_video')
def proxy_video():
    # JSONで取得した「本物のストリームURL」をここに入れる
    stream_url = request.args.get('stream_url')
    if not stream_url:
        return "Missing stream_url", 400

    proxies = {
        "http": PROXY_URL,
        "https": PROXY_URL,
    }
    
    headers = {
        'User-Agent': USER_AGENT,
        'Referer': 'https://www.pornhub.com/'
    }

    # プロキシ経由でストリームデータを取得し、そのままユーザーに流す（ストリーミング）
    req = requests.get(stream_url, proxies=proxies, headers=headers, stream=True, verify=False)
    
    return Response(
        req.iter_content(chunk_size=1024*10),
        content_type=req.headers.get('Content-Type'),
        headers={key: value for key, value in req.headers.items() if key.lower() in ['content-length', 'content-range', 'accept-ranges']}
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
