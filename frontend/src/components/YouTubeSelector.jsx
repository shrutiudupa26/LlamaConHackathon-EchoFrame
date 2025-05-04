import React, { useState } from 'react';

function YouTubeSelector({ onVideosSelected }) {
  const [url, setUrl] = useState('');
  const [videos, setVideos] = useState([]);

  const addVideo = () => {
    if (url.trim() && isValidYouTubeUrl(url)) {
      const updatedVideos = [...videos, url.trim()];
      setVideos(updatedVideos);
      onVideosSelected(updatedVideos);
      setUrl('');
    }
  };

  const removeVideo = (index) => {
    const updatedVideos = videos.filter((_, i) => i !== index);
    setVideos(updatedVideos);
    onVideosSelected(updatedVideos);
  };

  const isValidYouTubeUrl = (url) => {
    return /^https?:\/\/(www\.)?(youtube\.com|youtu\.be)\//.test(url);
  };

  return (
    <div className="youtube-selector">
      <input
        type="text"
        placeholder="Paste YouTube video URL"
        value={url}
        onChange={(e) => setUrl(e.target.value)}
      />
      <button onClick={addVideo}>Add</button>

      <ul>
        {videos.map((video, idx) => (
          <li key={idx}>
            {video}
            <button onClick={() => removeVideo(idx)}>Remove</button>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default YouTubeSelector;