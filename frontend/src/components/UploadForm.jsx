import React, { useState } from 'react';
import axios from 'axios';

export default function UploadForm() {
  const [fileType, setFileType] = useState('text');
  const [file, setFile] = useState(null);

  const handleUpload = async (e) => {
    e.preventDefault();
    const formData = new FormData();
    formData.append('file', file);

    let endpoint = `/upload/${fileType}`;
    try {
      await axios.post(`http://localhost:3001${endpoint}`, formData);
      alert(`${fileType.toUpperCase()} uploaded successfully!`);
    } catch (err) {
      alert('Upload failed');
      console.error(err);
    }
  };
  

  return (
    <form onSubmit={handleUpload}>
      <div className="form-group">
        <label className="form-label">File Type</label>
        <select 
          className="select"
          value={fileType} 
          onChange={(e) => setFileType(e.target.value)}
        >
          <option value="text">Text (PDF/MD)</option>
          <option value="image">Image</option>
          <option value="audio">Audio</option>
        </select>
      </div>

      <div className="form-group">
        <label className="form-label">Upload File</label>
        <div className="file-input-wrapper">
          <input 
            type="file" 
            className="file-input"
            onChange={(e) => setFile(e.target.files[0])} 
          />
          <div className="file-input-content">
            <svg xmlns="http://www.w3.org/2000/svg" className="button-icon" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 16.5V9.75m0 0l3 3m-3-3l-3 3M6.75 19.5a4.5 4.5 0 01-1.41-8.775 5.25 5.25 0 0110.233-2.33 3 3 0 013.758 3.848A3.752 3.752 0 0118 19.5H6.75z" />
            </svg>
            <span>{file ? file.name : 'Drop your file here or click to browse'}</span>
          </div>
        </div>
        <p className="form-hint">Supported formats: PDF, MD, MP3, WAV, PNG, JPG</p>
      </div>

      <button 
        type="submit" 
        className="button button-primary"
        disabled={!file}
      >
        <svg xmlns="http://www.w3.org/2000/svg" className="button-icon" viewBox="0 0 24 24" fill="currentColor">
          <path d="M11.47 1.72a.75.75 0 011.06 0l3 3a.75.75 0 01-1.06 1.06l-1.72-1.72V7.5h-1.5V4.06L9.53 5.78a.75.75 0 01-1.06-1.06l3-3zM11.25 7.5V15a.75.75 0 001.5 0V7.5h3.75a3 3 0 013 3v9a3 3 0 01-3 3h-9a3 3 0 01-3-3v-9a3 3 0 013-3h3.75z" />
        </svg>
        Upload File
      </button>
    </form>
  );
}