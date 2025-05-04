import React, { useState } from 'react';
import axios from 'axios';

export default function QuestionBox({ onAnswer }) {
  const [question, setQuestion] = useState('');

  const handleAsk = async () => {
    try {
      //const res = await axios.post('http://localhost:3001/api/ask', { question }); NODEJS
      const res = await axios.post('http://localhost:8000/ask', { question });
      onAnswer(res.data.response);
    } catch (err) {
      alert('Query failed');
      console.error(err);
    }
  };

  return (
    <div className="form-group">
      <textarea
        className="textarea"
        rows={3}
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        placeholder="Ask your question..."
      />
      <button 
        className="button button-primary"
        onClick={handleAsk}
        disabled={!question.trim()}
      >
        <svg xmlns="http://www.w3.org/2000/svg" className="button-icon" viewBox="0 0 24 24" fill="currentColor">
          <path d="M3.478 2.405a.75.75 0 00-.926.94l2.432 7.905H13.5a.75.75 0 010 1.5H4.984l-2.432 7.905a.75.75 0 00.926.94 60.519 60.519 0 0018.445-8.986.75.75 0 000-1.218A60.517 60.517 0 003.478 2.405z" />
        </svg>
        Ask Question
      </button>
    </div>
  );
}
