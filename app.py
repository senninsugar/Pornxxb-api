from flask import Flask, request, jsonify
import yt_dlp
import os

app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({"status": "active", "proxy": "ytproxy-siawaseok.duckdns.org:3007"})

@app.route('/get_info')
def get_info():
    video_url = request.args.get('url')
    if not video_url:
        return jsonify({"error": "Missing url parameter"}), 400

    # 指定されたプロキシ
    proxy_url = "http://ytproxy-siawaseok.duckdns.org:3007"

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'proxy': proxy_url,
        'nocheckcertificate': True,
        # リファラを固定して直リンク制限を回避しやすくする
        'referer': 'https://www.pornhub.com/',
        # 取得側と再生側でUser-Agentを合わせるための固定設定
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        'http_headers': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # download=Falseでメタデータ（JSON）のみ抽出
            info = ydl.extract_info(video_url, download=False)
            return jsonify(info)
    except Exception as e:
        return jsonify({
            "error": "Failed to bypass restriction",
            "details": str(e)
        }), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
