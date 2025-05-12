import React, { useState, useEffect, useCallback } from 'react';
import UploadForm from './components/UploadForm';
import QuestionBox from './components/QuestionBox';
import ResponseView from './components/ResponseViewer';
import YouTubeSelector from './components/YouTubeSelector';
import LiveVideo from './components/LiveVideo';
import './App.css';

function App() {
  const [response, setResponse] = useState('');
  const [summarization, setSummarization] = useState('');
  const [activeSection, setActiveSection] = useState('videos');
  const [showConversation, setShowConversation] = useState(false);

  // Handle both video selection and summarization results
  const handleVideosSelected = (videoList, summary) => {
    console.log('Selected videos:', videoList);
    if (summary) {
      console.log('Video summarization completed');
      setSummarization(summary);
      setActiveSection('question');
    }
  };

  // Handle section changes
  const handleSectionChange = useCallback((newSection) => {
    console.log('Switching from', activeSection, 'to', newSection);
    if (activeSection === 'conversation' && newSection !== 'conversation') {
      console.log('Leaving conversation section');
      // First set showConversation to false to trigger cleanup
      setShowConversation(false);
      // Then change the section after a small delay
      setTimeout(() => {
        setActiveSection(newSection);
      }, 100);
    } else {
      setActiveSection(newSection);
    }
  }, [activeSection]);

  // Effect to handle conversation visibility
  useEffect(() => {
    if (activeSection === 'conversation') {
      setShowConversation(true);
    }
  }, [activeSection]);

  const renderSection = () => {
    switch (activeSection) {
      case 'videos':
        return (
          <div className="card full-width">
            <div className="section-title">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                <path d="M10.5 3a1.5 1.5 0 00-1.5 1.5v15a1.5 1.5 0 003 0v-15A1.5 1.5 0 0010.5 3zM4.5 3a1.5 1.5 0 00-1.5 1.5v15a1.5 1.5 0 003 0v-15A1.5 1.5 0 004.5 3zM16.5 3a1.5 1.5 0 00-1.5 1.5v15a1.5 1.5 0 003 0v-15A1.5 1.5 0 0016.5 3z" />
              </svg>
              <h2>Select YouTube Videos</h2>
            </div>
            <YouTubeSelector onVideosSelected={handleVideosSelected} />
          </div>
        );
      case 'question':
        return (
          <div className="card full-width">
            <div className="section-title">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2.25c-2.429 0-4.817.178-7.152.521C2.87 3.061 1.5 4.795 1.5 6.741v6.018c0 1.946 1.37 3.68 3.348 3.97.877.129 1.761.234 2.652.316V21a.75.75 0 001.28.53l4.184-4.183a.39.39 0 01.266-.112c2.006-.05 3.982-.22 5.922-.506 1.978-.29 3.348-2.023 3.348-3.97V6.741c0-1.947-1.37-3.68-3.348-3.97A49.145 49.145 0 0012 2.25z" />
              </svg>
              <h2>Ask a Question</h2>
            </div>
            <QuestionBox onAnswer={setResponse} response={response} />
          </div>
        );
      case 'podcast':
        return (
          <div className="card full-width">
            <div className="section-title">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                <path d="M5.625 1.5c-1.036 0-1.875.84-1.875 1.875v17.25c0 1.035.84 1.875 1.875 1.875h12.75c1.035 0 1.875-.84 1.875-1.875V12.75A3.75 3.75 0 0016.5 9h-1.875a1.875 1.875 0 01-1.875-1.875V5.25A3.75 3.75 0 009 1.5H5.625z" />
              </svg>
              <h2>Podcast</h2>
            </div>
            <ResponseView response={response || summarization} />
          </div>
        );
      case 'conversation':
        return (
          <div className="card full-width">
            <div className="section-title">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                <path d="M4.5 3A1.5 1.5 0 003 4.5v15A1.5 1.5 0 004.5 21h15a1.5 1.5 0 001.5-1.5v-15A1.5 1.5 0 0019.5 3h-15z" />
              </svg>
              <h2>Live Video Conversation</h2>
            </div>
            {showConversation && <LiveVideo isActive={activeSection === 'conversation'} />}
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="app-header-content">
          <a href="/" className="app-logo">EchoFrame</a>
          <nav className="app-nav">
            <button 
              className={`nav-button ${activeSection === 'videos' ? 'active' : ''}`}
              onClick={() => handleSectionChange('videos')}
            >
              Videos
            </button>
            <button 
              className={`nav-button ${activeSection === 'question' ? 'active' : ''}`}
              onClick={() => handleSectionChange('question')}
            >
              Ask
            </button>
            <button 
              className={`nav-button ${activeSection === 'podcast' ? 'active' : ''}`}
              onClick={() => handleSectionChange('podcast')}
            >
              Podcast
            </button>
            <button 
              className={`nav-button ${activeSection === 'conversation' ? 'active' : ''}`}
              onClick={() => handleSectionChange('conversation')}
            >
              Conversation
            </button>
            <a 
              href="http://localhost:8000/docs" 
              target="_blank" 
              rel="noopener noreferrer"
              className="button button-secondary"
            >
              Documentation
            </a>
          </nav>
        </div>
      </header>

      <main className="app-main">
        <div className="app-main-content">
          {renderSection()}
        </div>
      </main>
    </div>
  );
}

export default App;