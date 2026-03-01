from flask import Flask, request, jsonify
from flask_cors import CORS
from services import search_videos

app = Flask(__name__)
CORS(app)

@app.route("/api/search")
def search():
    query = request.args.get("q", "")
    if not query:
        return jsonify([])

    results = search_videos(query)
    return jsonify(results)

if __name__ == "__main__":
    app.run(debug=True, port=5000)