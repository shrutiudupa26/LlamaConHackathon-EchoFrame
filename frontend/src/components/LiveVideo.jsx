import React, { useState, useEffect, useCallback, useRef } from 'react';

// Language options matching podcast translations
const LANGUAGE_OPTIONS = {
  en: 'English',
  es: 'Spanish',
  de: 'German',
  hi: 'Hindi'
};

export default function LiveVideo({ isActive }) {
  const [selectedLanguage, setSelectedLanguage] = useState('en');
  const [conversationUrl, setConversationUrl] = useState('');
  const [conversationId, setConversationId] = useState('');
  const [name, setName] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const cleanupAttempted = useRef(false);
  const previousIsActive = useRef(isActive);

  const handleLanguageChange = (e) => {
    setSelectedLanguage(e.target.value);
  };

  // Cleanup function to end conversation
  const endConversation = useCallback(async () => {
    if (conversationId && !cleanupAttempted.current) {
      cleanupAttempted.current = true;
      console.log('Attempting to end conversation:', conversationId);
      try {
        const response = await fetch(`http://localhost:8000/end-conversation/${conversationId}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
        });

        if (!response.ok) {
          const errorText = await response.text();
          console.error('Failed to end conversation:', errorText);
        } else {
          console.log('Successfully ended conversation:', conversationId);
          setConversationId('');
          setConversationUrl('');
        }
      } catch (error) {
        console.error('Error ending conversation:', error);
      } finally {
        // Reset cleanup flag after a delay to allow for retries if needed
        setTimeout(() => {
          cleanupAttempted.current = false;
        }, 1000);
      }
    }
  }, [conversationId]);

  // Effect to handle isActive changes
  useEffect(() => {
    console.log('isActive changed:', isActive, 'previous:', previousIsActive.current);
    if (previousIsActive.current && !isActive) {
      console.log('Section changed, ending conversation');
      endConversation();
    }
    previousIsActive.current = isActive;
  }, [isActive, endConversation]);

  // Cleanup effect when component unmounts or when switching away
  useEffect(() => {
    const cleanup = () => {
      console.log('Cleanup effect triggered for conversation:', conversationId);
      if (conversationId) {
        endConversation();
      }
    };

    // Add beforeunload event listener
    window.addEventListener('beforeunload', cleanup);

    // Return cleanup function
    return () => {
      window.removeEventListener('beforeunload', cleanup);
      cleanup();
    };
  }, [conversationId, endConversation]);

  // Additional effect to handle visibility changes
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden && conversationId) {
        console.log('Page hidden, ending conversation:', conversationId);
        endConversation();
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [conversationId, endConversation]);

  // Effect to handle component unmounting specifically
  useEffect(() => {
    return () => {
      if (conversationId) {
        console.log('Component unmounting, ending conversation:', conversationId);
        endConversation();
      }
    };
  }, [conversationId, endConversation]);

  const handleApplyLanguage = async () => {
    if (!name.trim()) {
      setError('Please enter your name');
      return;
    }
    
    setError('');
    setIsLoading(true);
    
    try {
      const response = await fetch('http://localhost:8000/start-conversation', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          language: LANGUAGE_OPTIONS[selectedLanguage],
          person: name.trim()
        }),
      });
      
      const text = await response.text();
      let data;
      
      try {
        data = JSON.parse(text);
      } catch (parseError) {
        console.error('Failed to parse JSON:', text);
        setError('Failed to parse server response');
        setIsLoading(false);
        return;
      }
      
      if (!response.ok) {
        console.error('API error:', data);
        
        if (data && data.message && data.message.includes('maximum concurrent conversations')) {
          setError('You have reached the maximum number of concurrent conversations. Please end some existing conversations before starting a new one.');
        } else if (data && data.message) {
          setError(`Error: ${data.message}`);
        } else {
          setError(`Error: ${response.status} ${response.statusText}`);
        }
        
        setConversationUrl('');
        setConversationId('');
        setIsLoading(false);
        return;
      }
      
      console.log('Raw API response:', data);
      
      // Check if the response contains the conversation URL and ID
      if (data && data.conversation_url && data.conversation_id) {
        console.log('Setting conversation URL:', data.conversation_url);
        setConversationUrl(data.conversation_url);
        setConversationId(data.conversation_id);
        setError('');
      } else if (data.error) {
        setError(`API Error: ${data.error}`);
        setConversationUrl('');
        setConversationId('');
      } else {
        console.error('Unexpected response format:', data);
        setError('No conversation URL in response');
        setConversationUrl('');
        setConversationId('');
      }
    } catch (error) {
      console.error('Error starting conversation:', error);
      setError(`Error: ${error.message}`);
      setConversationUrl('');
      setConversationId('');
    } finally {
      setIsLoading(false);
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
          {Object.entries(LANGUAGE_OPTIONS).map(([code, name]) => (
            <option key={code} value={code}>{name}</option>
          ))}
        </select>
        <button 
          className="button button-primary" 
          onClick={handleApplyLanguage}
          disabled={!name.trim() || isLoading}
        >
          {isLoading ? 'Starting...' : 'Start Conversation'}
        </button>
      </div>

      {error && (
        <div style={{ 
          padding: '1rem', 
          backgroundColor: '#fee2e2', 
          color: '#b91c1c', 
          borderRadius: '4px', 
          marginBottom: '1rem' 
        }}>
          {error}
        </div>
      )}

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