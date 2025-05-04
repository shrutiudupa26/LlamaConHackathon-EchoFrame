import React, { useState, useEffect } from 'react';

export default function ResponseViewer() {
  const [language, setLanguage] = useState('en');
  const [englishText, setEnglishText] = useState('');
  const [translatedText, setTranslatedText] = useState('');
  const [loadingAudio, setLoadingAudio] = useState(false);

  // Fetch English podcast text on mount
  useEffect(() => {
    const fetchEnglishText = async () => {
      try {
        const res = await fetch('http://localhost:8000/podcast-text?lang=en');
        if (!res.ok) throw new Error('Failed to fetch English podcast text');
        const text = await res.text();
        setEnglishText(text);
      } catch (err) {
        console.error(err);
        setEnglishText('Error loading English content.');
      }
    };
    fetchEnglishText();
  }, []);

  const handleLanguageChange = async (e) => {
    const selectedLang = e.target.value;
    setLanguage(selectedLang);

    if (selectedLang === 'en') {
      setTranslatedText('');
      return;
    }

    try {
      const res = await fetch('http://localhost:8000/test-translations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ language: selectedLang }),
      });

      if (!res.ok) throw new Error('Failed to fetch translation');
      const text = await res.text();
      setTranslatedText(text);
    } catch (err) {
      console.error(err);
      setTranslatedText('Error loading translated content.');
    }
  };

  const handlePlayClick = async () => {
    setLoadingAudio(true);
    try {
      const res = await fetch('http://localhost:8000/generate_speech', { method: 'POST' });
      if (!res.ok) throw new Error('Failed to trigger speech generation');

      const blob = await res.blob();
      const audioUrl = URL.createObjectURL(blob);
      new Audio(audioUrl).play();
    } catch (err) {
      console.error(err);
      alert('Failed to play audio');
    } finally {
      setLoadingAudio(false);
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

        <button onClick={handlePlayClick} disabled={loadingAudio} className="play-button">
          {loadingAudio ? 'Playing...' : 'Play'}
        </button>
      </div>

      <div className="language-block">
        <h4>English</h4>
        <pre className="response-content">{englishText}</pre>
      </div>

      {language !== 'en' && (
        <div className="language-block">
          <h4>Translated ({language})</h4>
          <pre className="response-content">{translatedText}</pre>
        </div>
      )}
    </div>
  );
}