from flask import Flask, request, Response, jsonify
import yt_dlp
import requests
import os
import re
from urllib.parse import urljoin, quote

app = Flask(__name__)

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
        'referer': 'https://www.google.com/', # 汎用的なリファラ
        'nocheckcertificate': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            
            # m3u8のURLを探す
            manifest_url = info.get('url')
            if '.m3u8' in manifest_url:
                # 自身のproxy_m3u8エンドポイントを指すように変換
                proxy_m3u8_url = f"{request.host_url}proxy_m3u8?stream_url={quote(manifest_url)}"
                return jsonify({"manifest_url": proxy_m3u8_url, "title": info.get('title')})
            
            return jsonify(info)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/proxy_m3u8')
def proxy_m3u8():
    stream_url = request.args.get('stream_url')
    if not stream_url:
        return "Missing stream_url", 400

    proxies = {"http": PROXY_URL, "https": PROXY_URL}
    headers = {'User-Agent': USER_AGENT, 'Referer': 'https://www.google.com/'}

    try:
        resp = requests.get(stream_url, proxies=proxies, headers=headers, verify=False, timeout=10)
        content = resp.text

        # m3u8内の相対パスや絶対パスを、全てこのサーバー経由(proxy_video)に書き換える
        base_url = stream_url.rsplit('/', 1)[0] + '/'
        new_content = []
        
        for line in content.splitlines():
            if line.startswith('#') or not line.strip():
                new_content.append(line)
            else:
                # URLを絶対パスに変換
                full_url = urljoin(base_url, line.strip())
                # セグメントファイル(.tsなど)もこのサーバー経由で配信
                proxy_url = f"{request.host_url}proxy_video?stream_url={quote(full_url)}"
                new_content.append(proxy_url)

        return Response("\n".join(new_content), content_type='application/vnd.apple.mpegurl')
    except Exception as e:
        return str(e), 500

@app.route('/proxy_video')
def proxy_video():
    stream_url = request.args.get('stream_url')
    if not stream_url:
        return "Missing stream_url", 400

    proxies = {"http": PROXY_URL, "https": PROXY_URL}
    headers = {
        'User-Agent': USER_AGENT,
        'Range': request.headers.get('Range', '')
    }

    req = requests.get(stream_url, proxies=proxies, headers=headers, stream=True, verify=False, timeout=15)
    
    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    response_headers = [(name, value) for (name, value) in req.raw.headers.items()
                        if name.lower() not in excluded_headers]

    def generate():
        for chunk in req.iter_content(chunk_size=65536):
            yield chunk

    return Response(generate(), status=req.status_code, content_type=req.headers.get('Content-Type'), headers=response_headers)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
