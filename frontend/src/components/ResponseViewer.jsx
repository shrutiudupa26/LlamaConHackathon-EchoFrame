import React from 'react';

export default function ResponseViewer({ response }) {
  return (
    <div>
      <h3>Answer:</h3>
      <pre style={{ whiteSpace: 'pre-wrap' }}>{response}</pre>
    </div>
  );
}