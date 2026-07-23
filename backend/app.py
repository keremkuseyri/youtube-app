from flask import Flask, request, jsonify
from flask_cors import CORS
from config import Config
from services import search_videos

app = Flask(__name__)
CORS(app)


@app.route("/healthz")
def healthz():
    return jsonify({"status": "ok"})

@app.route("/api/search")
def search():
    query = request.args.get("q", "")
    if not query:
        return jsonify([])

    results = search_videos(query)
    return jsonify(results)

if __name__ == "__main__":
    port = int(__import__("os").getenv("PORT", 5000))
    app.run(debug=Config.DEBUG, host="0.0.0.0", port=port)