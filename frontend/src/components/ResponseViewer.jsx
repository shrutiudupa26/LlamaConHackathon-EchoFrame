import React, { useState } from 'react';

export default function ResponseViewer({ response: initialResponse }) {
  const [language, setLanguage] = useState('en');
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState(initialResponse);

  const handleLanguageChange = async (e) => {
    const selectedLang = e.target.value;
    setLanguage(selectedLang);
    
    try {
      const res = await fetch(`http://localhost:8000/podcast-text?lang=${selectedLang}`);
      if (!res.ok) {
        throw new Error('Failed to fetch podcast text');
      }
      const text = await res.text();
      setResponse(text);
    } catch (error) {
      console.error('Error fetching podcast text:', error);
      setResponse('Failed to load podcast text.');
    }
  };

  const handlePlayClick = async () => {
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/generate_speech', {
        method: 'POST',
      });

      if (!res.ok) {
        throw new Error('Failed to trigger speech generation');
      }

      const blob = await res.blob();
      const audioUrl = URL.createObjectURL(blob);
      const audio = new Audio(audioUrl);
      audio.play();
    } catch (error) {
      console.error('Error:', error);
      alert('Failed to play audio');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="response-viewer">
      <div className="response-header">
        <label htmlFor="language-select">Language: </label>
        <select
          id="language-select"
          value={language}
          onChange={handleLanguageChange}
          className="language-dropdown"
        >
          <option value="en">English</option>
          <option value="es">Spanish</option>
          <option value="fr">French</option>
          <option value="hi">Hindi</option>
          <option value="zh">Chinese</option>
        </select>

        <button onClick={handlePlayClick} disabled={loading} className="play-button">
          {loading ? 'Playing...' : 'Play'}
        </button>
      </div>

      {response ? (
        <pre className="response-content">{response}</pre>
      ) : (
        <div className="response-placeholder">
          <svg xmlns="http://www.w3.org/2000/svg" className="response-icon" viewBox="0 0 24 24" fill="currentColor">
            <path d="M21.731 2.269a2.625 2.625 0 00-3.712 0l-1.157 1.157 3.712 3.712 1.157-1.157a2.625 2.625 0 000-3.712zM19.513 8.199l-3.712-3.712-12.15 12.15a5.25 5.25 0 00-1.32 2.214l-.8 2.685a.75.75 0 00.933.933l2.685-.8a5.25 5.25 0 002.214-1.32L19.513 8.2z" />
          </svg>
          <p>Your answer will appear here</p>
        </div>
      )}
    </div>
  );
}