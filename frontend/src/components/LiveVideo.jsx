import React, { useState } from 'react';

export default function LiveVideo() {
  const [selectedLanguage, setSelectedLanguage] = useState('English');
  const [conversationUrl, setConversationUrl] = useState('');
  const [name, setName] = useState('');

  const handleLanguageChange = (e) => {
    setSelectedLanguage(e.target.value);
  };

  const handleApplyLanguage = async () => {
    try {
      const response = await fetch('http://localhost:8000/start-conversation', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          language: selectedLanguage,
          person: name.trim()
        }),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const text = await response.text();
      if (!text) {
        throw new Error('Empty response received');
      }
      
      try {
        const data = JSON.parse(text);
        console.log('Raw API response:', data);
        
        // Check if the response contains the conversation URL directly or nested
        if (data && data.conversation_url) {
          console.log('Setting conversation URL:', data.conversation_url);
          setConversationUrl(data.conversation_url);
        } else if (data.error) {
          throw new Error(`API Error: ${data.error}`);
        } else {
          console.error('Unexpected response format:', data);
          throw new Error('No conversation URL in response');
        }
      } catch (parseError) {
        console.error('Failed to parse JSON:', text);
        throw parseError;
      }
    } catch (error) {
      console.error('Error starting conversation:', error);
      // You might want to show an error message to the user here
      setConversationUrl('');
    }
  };

  return (
    <div>
      <div style={{ marginBottom: '1rem', display: 'flex', gap: '1rem', alignItems: 'center' }}>
        <input
          type="text"
          placeholder="Enter your name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          style={{ padding: '0.5rem', borderRadius: '4px', border: '1px solid #ccc' }}
        />
        <select value={selectedLanguage} onChange={handleLanguageChange}>
          <option value="English">English</option>
          <option value="Spanish">Spanish</option>
          <option value="French">French</option>
          <option value="German">German</option>
          <option value="Urdu">Urdu</option>
          <option value="Hindi">Hindi</option>
        </select>
        <button 
          className="button button-primary" 
          onClick={handleApplyLanguage}
          disabled={!name.trim()}
        >
          Start Conversation
        </button>
      </div>

      {conversationUrl && (
        <iframe
          src={conversationUrl}
          width="100%"
          height="600"
          allow="camera; microphone; fullscreen; display-capture"
          style={{ border: "1px solid #ccc", borderRadius: "8px" }}
          title="Tavus Conversation"
        />
      )}
    </div>
  );
}