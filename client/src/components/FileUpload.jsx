import React, { useState } from 'react';
import axios from 'axios';

function FileUpload({ strategy, onUploadComplete, token }) {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setError(null);
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return;

    setUploading(true);
    setError(null);
    const formData = new FormData();
    formData.append('file', file);

    try {
      let endpoint = '';
      if (strategy.toLowerCase() === 'llamaparse') {
        endpoint = 'http://127.0.0.1:8000/llamaparse/indexing';
      } else if (strategy.toLowerCase() === 'graphrag') {
        endpoint = 'http://127.0.0.1:8000/graphrag/indexing';
      } else if (strategy.toLowerCase() === 'vision-pdf-rag') {
        endpoint = 'http://127.0.0.1:8000/multimodal_rag/upload_pdf';
      } else {
        throw new Error(`Invalid strategy: ${strategy}`);
      }

      const response = await axios.post(endpoint, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          'Authorization': `Bearer ${token}`,
        },
      });
      onUploadComplete(response.data);
    } catch (error) {
      console.error('Error uploading file:', error);
      setError(error.response?.data?.detail || error.message || 'An error occurred while uploading the file.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <h2 className="text-xl font-semibold mb-4">Upload New Document</h2>
      <p className="mb-4">Selected strategy: {strategy}</p>
      <form onSubmit={handleUpload}>
        <input
          type="file"
          onChange={handleFileChange}
          className="mb-4 p-2 border rounded w-full"
        />
        <button
          type="submit"
          disabled={!file || uploading}
          className={`w-full bg-blue-500 text-white py-2 px-4 rounded ${
            !file || uploading ? 'opacity-50 cursor-not-allowed' : 'hover:bg-blue-600'
          }`}
        >
          {uploading ? 'Uploading...' : 'Upload'}
        </button>
      </form>
      {error && <p className="text-red-500 mt-2">{error}</p>}
    </div>
  );
}

export default FileUpload;