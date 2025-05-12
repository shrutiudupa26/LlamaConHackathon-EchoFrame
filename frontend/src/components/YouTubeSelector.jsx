import React, { useState } from 'react';

function YouTubeSelector({ onVideosSelected }) {
  const [url, setUrl] = useState('');
  const [videos, setVideos] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingStatus, setProcessingStatus] = useState('');

  const addVideo = async () => {
    if (url.trim() && isValidYouTubeUrl(url)) {
      try {
        const videoId = extractVideoId(url.trim());
        const videoTitle = await fetchVideoTitle(videoId);
        const videoData = {
          url: url.trim(),
          title: videoTitle || 'Untitled Video'
        };
        const updatedVideos = [...videos, videoData];
        setVideos(updatedVideos);
        onVideosSelected(updatedVideos.map(v => v.url));
        setUrl('');
      } catch (error) {
        console.error('Error adding video:', error);
      }
    }
  };

  const removeVideo = (index) => {
    const updatedVideos = videos.filter((_, i) => i !== index);
    setVideos(updatedVideos);
    onVideosSelected(updatedVideos.map(v => v.url));
  };

  const isValidYouTubeUrl = (url) => {
    return /^https?:\/\/(www\.)?(youtube\.com|youtu\.be)\//.test(url);
  };

  const extractVideoId = (url) => {
    let videoId = '';
    if (url.includes('youtu.be/')) {
      videoId = url.split('youtu.be/')[1].split('?')[0];
    } else if (url.includes('watch?v=')) {
      videoId = url.split('watch?v=')[1].split('&')[0];
    } else if (url.includes('/shorts/')) {
      videoId = url.split('/shorts/')[1].split('?')[0].split('&')[0];
    }
    return videoId;
  };

  const fetchVideoTitle = async (videoId) => {
    try {
      const response = await fetch(`https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v=${videoId}&format=json`);
      if (response.ok) {
        const data = await response.json();
        return data.title;
      }
      return null;
    } catch (error) {
      console.error('Error fetching video title:', error);
      return null;
    }
  };

  const handleProcessVideos = async () => {
    if (videos.length === 0) {
      alert('Please add at least one video URL');
      return;
    }
    
    setIsProcessing(true);
    setProcessingStatus('Processing videos...');
    
    try {
      const res = await fetch('http://localhost:8000/process-videos', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ videos: videos.map(v => v.url) }),
      });
      
      if (!res.ok) throw new Error('Failed to process videos');
      
      const data = await res.json();
      
      if (data.summarization && data.summarization.response) {
        setProcessingStatus('Videos processed and summarized successfully!');
        if (typeof onVideosSelected === 'function') {
          onVideosSelected(videos.map(v => v.url), data.summarization.response);
        }
      } else if (data.summarization && data.summarization.error) {
        setProcessingStatus(`Videos processed, but summarization failed: ${data.summarization.error}`);
        console.error('Summarization error:', data.summarization.error);
      } else {
        setProcessingStatus('Videos processed successfully!');
      }
      
    } catch (err) {
      setProcessingStatus('Processing failed');
      console.error(err);
    } finally {
      setTimeout(() => {
        setIsProcessing(false);
        setProcessingStatus('');
      }, 3000);
    }
  };

  return (
    <div className="youtube-selector">
      <div className="url-input-group">
        <input
          type="text"
          placeholder="Paste YouTube video URL"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          disabled={isProcessing}
          className="url-input"
        />
        <button 
          onClick={addVideo} 
          disabled={isProcessing || !url.trim() || !isValidYouTubeUrl(url)}
          className="button button-primary"
        >
          Add
        </button>
      </div>

      {videos.length > 0 && (
        <div className="video-list">
          <h3>Added Videos:</h3>
          <ul>
            {videos.map((video, idx) => (
              <li key={idx} className="video-item">
                <span className="video-title">{video.title}</span>
                <button 
                  onClick={() => removeVideo(idx)}
                  disabled={isProcessing}
                  className="button button-secondary"
                >
                  Remove
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
      
      {isProcessing ? (
        <div className="processing-indicator">
          <div className="spinner"></div>
          <p>{processingStatus || 'Processing videos... This may take a few minutes.'}</p>
        </div>
      ) : (
        <>
          {processingStatus && (
            <div className="processing-status">
              <p>{processingStatus}</p>
            </div>
          )}
          {videos.length > 0 && (
            <button 
              className="button button-primary process-button"
              onClick={handleProcessVideos}
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="button-icon" viewBox="0 0 24 24" fill="currentColor">
                <path d="M3.478 2.405a.75.75 0 00-.926.94l2.432 7.905H13.5a.75.75 0 010 1.5H4.984l-2.432 7.905a.75.75 0 00.926.94 60.519 60.519 0 0018.445-8.986.75.75 0 000-1.218A60.517 60.517 0 003.478 2.405z" />
              </svg>
              Process Videos
            </button>
          )}
        </>
      )}
    </div>
  );
}

export default YouTubeSelector;