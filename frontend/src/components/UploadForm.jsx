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
      <label>
        File Type:
        <select value={fileType} onChange={(e) => setFileType(e.target.value)}>
          <option value="text">Text (PDF/MD)</option>
          <option value="image">Image</option>
          <option value="audio">Audio</option>
        </select>
      </label>
      <input type="file" onChange={(e) => setFile(e.target.files[0])} />
      <button type="submit">Upload</button>
    </form>
  );
}