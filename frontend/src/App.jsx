import React, { useState } from 'react';
import UploadForm from './components/UploadForm';
import QuestionBox from './components/QuestionBox';
import ResponseView from './components/ResponseViewer';
import './App.css';

function App() {
  const [response, setResponse] = useState('');

  return (
    <div id="root">
      <h1>EchoFrame</h1>

      <section>
        <h2>Upload Your File</h2>
        <UploadForm />
      </section>

      <section>
        <h2>Ask a Question</h2>
        <QuestionBox onAnswer={setResponse} />
      </section>

      <section>
        <h2>Response</h2>
        <ResponseView response={response} />
      </section>
    </div>
  );
}

export default App;