import React, { useState } from 'react';

export default function LiveVideo() {
  const [selectedLanguage, setSelectedLanguage] = useState('en');

  const handleLanguageChange = (e) => {
    setSelectedLanguage(e.target.value);
  };

  const handleApplyLanguage = () => {
    console.log('Selected language:', selectedLanguage);
    // You could trigger subtitle update or model language change here
  };

  return (
    <div>
      <div style={{ marginBottom: '1rem', display: 'flex', gap: '1rem', alignItems: 'center' }}>
        <select value={selectedLanguage} onChange={handleLanguageChange}>
          <option value="en">English</option>
          <option value="es">Spanish</option>
          <option value="fr">French</option>
          <option value="de">German</option>
          <option value="ur">Urdu</option>
          <option value="hi">Hindi</option>
        </select>
        <button className="button button-primary" onClick={handleApplyLanguage}>
          Start Conversation
        </button>
      </div>

      <iframe
        src="https://tavus.daily.co/c31c3a261f89"
        width="100%"
        height="600"
        allow="camera; microphone; fullscreen; display-capture"
        style={{ border: "1px solid #ccc", borderRadius: "8px" }}
        title="Tavus Conversation"
      />
    </div>
  );
}