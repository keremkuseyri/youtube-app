import { useState } from "react";
import { searchVideos } from "./api";
import VideoCard from "./components/VideoCard";
import "./App.css";

export default function App() {
  const [query, setQuery] = useState("");
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [hasSearched, setHasSearched] = useState(false);

  const handleSearch = async (event) => {
    event.preventDefault();
    const trimmedQuery = query.trim();

    if (!trimmedQuery) {
      setVideos([]);
      setHasSearched(false);
      setError("");
      return;
    }

    try {
      setLoading(true);
      setError("");
      setHasSearched(true);
      const data = await searchVideos(trimmedQuery);
      setVideos(data);
    } catch {
      setVideos([]);
      setError("Couldn’t fetch videos right now. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="yt-page">
      <header className="yt-topbar">
        <div className="yt-brand">LearnTube</div>

        <form className="yt-search-wrap" onSubmit={handleSearch}>
          <label htmlFor="query" className="sr-only">
            Search query
          </label>
          <input
            id="query"
            className="yt-search-input"
            placeholder="Search educational videos"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <button className="yt-search-button" type="submit" disabled={loading}>
            {loading ? "Searching..." : "Search"}
          </button>
        </form>
      </header>

      <main className="yt-content">
        {error && <p className="state-message error-message">{error}</p>}

        {!loading && hasSearched && videos.length === 0 && !error && (
          <p className="state-message">No videos found. Try a different query.</p>
        )}

        <div className="results-header">
          <h2>Top results for you</h2>
          <span>{videos.length} videos</span>
        </div>

        <div className="results-grid">
          {videos.map((video) => (
            <VideoCard key={video.id} video={video} />
          ))}
        </div>

        {loading && (
          <div className="loading-grid" aria-live="polite">
            {[...Array(6)].map((_, index) => (
              <div className="skeleton-card" key={index} />
            ))}
          </div>
        )}
      </main>
    </div>
  );
}