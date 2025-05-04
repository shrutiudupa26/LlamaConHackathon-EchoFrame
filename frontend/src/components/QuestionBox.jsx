import React, { useState } from 'react';
import axios from 'axios';

export default function QuestionBox({ onAnswer }) {
  const [question, setQuestion] = useState('');

  const handleAsk = async () => {
    try {
      const res = await axios.post('http://localhost:3001/api/ask', { question });
      onAnswer(res.data.answer);
    } catch (err) {
      alert('Query failed');
      console.error(err);
    }
  };

  return (
    <div>
      <textarea
        rows={3}
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        placeholder="Ask your question..."
      />
      <br />
      <button onClick={handleAsk}>Ask</button>
    </div>
  );
}
