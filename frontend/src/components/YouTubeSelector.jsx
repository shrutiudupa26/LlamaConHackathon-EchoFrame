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

  const handleAsk = () => {
    // Handle the action when the user clicks "Ask Question"
    // This could involve sending the selected videos to a backend or processing them
    console.log('Selected videos:', videos);
  }

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
      <button 
        className="button"
        onClick={handleAsk}
      >
        <svg xmlns="http://www.w3.org/2000/svg" className="button-icon" viewBox="0 0 24 24" fill="currentColor">
          <path d="M3.478 2.405a.75.75 0 00-.926.94l2.432 7.905H13.5a.75.75 0 010 1.5H4.984l-2.432 7.905a.75.75 0 00.926.94 60.519 60.519 0 0018.445-8.986.75.75 0 000-1.218A60.517 60.517 0 003.478 2.405z" />
        </svg>
        Process Videos
      </button>
    </div>
    
  );
}

export default YouTubeSelector;