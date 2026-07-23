import { useState } from "react";

export default function VideoCard({ video }) {
  const [previewing, setPreviewing] = useState(false);
  const embedUrl = `https://www.youtube.com/embed/${video.id}?autoplay=1&mute=0&controls=0&rel=0&modestbranding=1&loop=1&playlist=${video.id}&playsinline=1`;

  return (
    <article className="video-card">
      <a
        className="video-thumb-link"
        href={`https://youtube.com/watch?v=${video.id}`}
        target="_blank"
        rel="noreferrer"
        onMouseEnter={() => setPreviewing(true)}
        onMouseLeave={() => setPreviewing(false)}
        onFocus={() => setPreviewing(true)}
        onBlur={() => setPreviewing(false)}
      >
        {!previewing ? (
          <img
            src={video.thumbnail}
            alt={video.title}
            className="video-thumb"
            loading="lazy"
          />
        ) : (
          <iframe
            className="video-preview-frame"
            src={embedUrl}
            title={`Preview of ${video.title}`}
            allow="autoplay; encrypted-media; picture-in-picture"
            referrerPolicy="strict-origin-when-cross-origin"
          />
        )}
      </a>

      <div className="video-content">
        <h3 className="video-title">{video.title}</h3>
        <p className="video-channel">{video.channel}</p>

        <div className="video-meta-row">
          <span>{video.views} views</span>
          <span>{video.likes} likes</span>
          <span>{video.duration}</span>
        </div>

        <div className="video-score-pill">
          AI Quality Score
          <strong>{video.score}</strong>
        </div>
      </div>
    </article>
  );
}