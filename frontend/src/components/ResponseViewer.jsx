import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';

const LANGUAGE_OPTIONS = {
  en: 'English',
  es: 'Spanish',
  de: 'German',
  hi: 'Hindi'
};

export default function ResponseViewer({ response }) {
  const [language, setLanguage] = useState('en');
  const [englishText, setEnglishText] = useState('');
  const [translations, setTranslations] = useState({});
  const [loadingTranslation, setLoadingTranslation] = useState(false);
  const [loadingAudio, setLoadingAudio] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isPodcastAvailable, setIsPodcastAvailable] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const audioRef = useRef(null);

  // Function to fetch the podcast text
  const fetchEnglishText = async () => {
    try {
      setIsRefreshing(true);
      const res = await fetch('http://localhost:8000/podcast-text?lang=en');
      if (!res.ok) {
        if (res.status === 404) {
          setEnglishText('No podcast data available yet. Process videos first.');
          setIsPodcastAvailable(false);
          return;
        }
        throw new Error('Failed to fetch English podcast text');
      }
      const text = await res.text();
      setEnglishText(text);
      setIsPodcastAvailable(true);
    } catch (err) {
      console.error(err);
      setEnglishText('Error loading English content.');
      setIsPodcastAvailable(false);
    } finally {
      setIsRefreshing(false);
    }
  };

  // Fetch English podcast text on mount or when response changes
  useEffect(() => {
    if (!response) return; // Only fetch if there's a response
    fetchEnglishText();
  }, [response]);

  const handleLanguageChange = async (e) => {
    const selectedLang = e.target.value;
    setLanguage(selectedLang);

    if (selectedLang === 'en') {
      return;
    }

    if (!isPodcastAvailable) {
      return;
    }

    if (translations[selectedLang]) {
      return; // Translation already exists
    }

    setLoadingTranslation(true);
    try {
      const res = await fetch('http://localhost:8000/translate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          languages: [selectedLang]
        }),
      });

      if (!res.ok) throw new Error('Failed to fetch translation');
      const data = await res.json();
      
      if (data.translations && data.translations[selectedLang]) {
        setTranslations(prev => ({
          ...prev,
          [selectedLang]: data.translations[selectedLang]
        }));
      } else {
        throw new Error('Invalid translation response');
      }
    } catch (err) {
      console.error(err);
      setTranslations(prev => ({
        ...prev,
        [selectedLang]: 'Error loading translated content.'
      }));
    } finally {
      setLoadingTranslation(false);
    }
  };

  const handlePlayClick = async () => {
    if (!isPodcastAvailable) {
      alert('No podcast data available to play.');
      return;
    }

    // If audio is already playing, stop it
    if (audioRef.current) {
      handleStopClick();
      return;
    }

    setLoadingAudio(true);
    try {
      const res = await fetch('http://localhost:8000/generate-speech', {
        method: 'GET',
        headers: {
          'Accept': 'audio/wav',
        },
      });
      
      if (!res.ok) {
        const errorText = await res.text();
        throw new Error(errorText || 'Failed to fetch audio');
      }
      
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      
      audioRef.current = new Audio(url);
      audioRef.current.onended = () => {
        handleStopClick();
        URL.revokeObjectURL(url); // Clean up the URL when done
      };
      await audioRef.current.play();
      setIsPlaying(true);
    } catch (err) {
      console.error('Audio playback error:', err);
      alert('Error playing audio: ' + (err.message || 'Unknown error'));
      handleStopClick();
    } finally {
      setLoadingAudio(false);
    }
  };

  const handleStopClick = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0; // Reset playback position
      audioRef.current = null;
    }
    setIsPlaying(false);
  };

  // Clean up audio when component unmounts
  useEffect(() => {
    return () => {
      handleStopClick();
    };
  }, []);

  return (
    <div className="response-viewer">
      <div className="controls">
        <select 
          value={language} 
          onChange={handleLanguageChange}
          className="language-select"
          disabled={!isPodcastAvailable || loadingTranslation}
        >
          {Object.entries(LANGUAGE_OPTIONS).map(([code, name]) => (
            <option key={code} value={code}>{name}</option>
          ))}
        </select>
        
        <button
          onClick={isPlaying ? handleStopClick : handlePlayClick}
          disabled={!isPodcastAvailable || loadingAudio}
          className={`play-button ${isPlaying ? 'stop' : ''}`}
        >
          {loadingAudio ? 'Loading...' : isPlaying ? 'Stop Audio' : 'Play Audio'}
        </button>
        
        <button
          onClick={fetchEnglishText}
          disabled={isRefreshing}
          className="refresh-button"
        >
          {isRefreshing ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      <div className="language-block">
        <h4>English</h4>
        <pre className="response-content">{englishText || 'No content available.'}</pre>
      </div>

      {language !== 'en' && (
        <div className="language-block">
          <h4>{LANGUAGE_OPTIONS[language]}</h4>
          {loadingTranslation ? (
            <div className="loading">Translating...</div>
          ) : (
            <pre className="response-content">
              {translations[language] || 'No translation available.'}
            </pre>
          )}
        </div>
      )}
    </div>
  );
}