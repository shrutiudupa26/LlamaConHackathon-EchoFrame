import React, { useState } from 'react';
import UploadForm from './components/UploadForm';
import QuestionBox from './components/QuestionBox';
import ResponseView from './components/ResponseViewer';
import './App.css';

function App() {
  const [response, setResponse] = useState('');

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="app-header-content">
          <a href="/" className="app-logo">EchoFrame</a>
          <nav>
            <button className="button button-secondary">Documentation</button>
          </nav>
        </div>
      </header>

      <main className="app-main">
        <div className="card">
          <div className="section-title">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 16.5V9.75m0 0l3 3m-3-3l-3 3M6.75 19.5a4.5 4.5 0 01-1.41-8.775 5.25 5.25 0 0110.233-2.33 3 3 0 013.758 3.848A3.752 3.752 0 0118 19.5H6.75z" />
            </svg>
            <h2>Upload Your File</h2>
          </div>
          <UploadForm />
        </div>

        <div className="card">
          <div className="section-title">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2.25c-2.429 0-4.817.178-7.152.521C2.87 3.061 1.5 4.795 1.5 6.741v6.018c0 1.946 1.37 3.68 3.348 3.97.877.129 1.761.234 2.652.316V21a.75.75 0 001.28.53l4.184-4.183a.39.39 0 01.266-.112c2.006-.05 3.982-.22 5.922-.506 1.978-.29 3.348-2.023 3.348-3.97V6.741c0-1.947-1.37-3.68-3.348-3.97A49.145 49.145 0 0012 2.25z" />
            </svg>
            <h2>Ask a Question</h2>
          </div>
          <QuestionBox onAnswer={setResponse} />
        </div>

        <div className="card">
          <div className="section-title">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
              <path d="M5.625 1.5c-1.036 0-1.875.84-1.875 1.875v17.25c0 1.035.84 1.875 1.875 1.875h12.75c1.035 0 1.875-.84 1.875-1.875V12.75A3.75 3.75 0 0016.5 9h-1.875a1.875 1.875 0 01-1.875-1.875V5.25A3.75 3.75 0 009 1.5H5.625z" />
            </svg>
            <h2>Response</h2>
          </div>
          <ResponseView response={response} />
        </div>
      </main>
    </div>
  );
}

export default App;