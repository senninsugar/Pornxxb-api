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
        'Referer': 'https://www.pornhub.com/',
        'Range': request.headers.get('Range', '')
    }

    # プロキシ経由でストリームデータを取得し、そのままユーザーに流す（ストリーミング）
    # verify=FalseでSSL検証をスキップし、接続エラーを回避
    req = requests.get(stream_url, proxies=proxies, headers=headers, stream=True, verify=False, timeout=15)
    
    # 応答ヘッダーの構築（Node.jsプロキシの挙動に合わせ、必要なメタデータのみを転送）
    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    response_headers = [
        (name, value) for (name, value) in req.raw.headers.items()
        if name.lower() not in excluded_headers
    ]

    def generate():
        for chunk in req.iter_content(chunk_size=65536):
            yield chunk

    return Response(
        generate(),
        status=req.status_code,
        content_type=req.headers.get('Content-Type'),
        headers=response_headers
    )

@app.route('/search')
def search():
    query = request.args.get('q')
    results_limit = request.args.get('n', default=10, type=int) # デフォルト10件
    
    if not query:
        return jsonify({"error": "Missing query"}), 400

    # ytsearchの代わりにPornhub専用の検索キーワードを使用
    # 例: phsearch10:japanese
    search_url = f"phsearch{results_limit}:{query}"

    ydl_opts = {
        'quiet': True,
        'proxy': PROXY_URL,
        'user_agent': USER_AGENT,
        'referer': 'https://www.pornhub.com/',
        'nocheckcertificate': True,
        'extract_flat': True,  # 個別の動画解析をせず、メタデータだけを高速に取得
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # 検索結果のリストを取得
            info = ydl.extract_info(search_url, download=False)
            
            # 結果を使いやすい形に整形
            results = []
            if 'entries' in info:
                for entry in info['entries']:
                    results.append({
                        "title": entry.get("title"),
                        "url": entry.get("url"), # これを /get_info に渡せば詳細が取れる
                        "thumbnail": entry.get("thumbnail"),
                        "duration": entry.get("duration"),
                        "view_count": entry.get("view_count")
                    })

            return jsonify({
                "query": query,
                "results": results
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
