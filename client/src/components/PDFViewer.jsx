import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';

function PDFViewer({ document, token }) {
  const [pages, setPages] = useState([]);
  const [error, setError] = useState(null);
  const [inputMessage, setInputMessage] = useState('');
  const [selectedPage, setSelectedPage] = useState(null);
  const [isWaitingForResponse, setIsWaitingForResponse] = useState(false);
  const pageRefs = useRef({});
  const [imagesLoaded, setImagesLoaded] = useState(false);

  useEffect(() => {
    if (document && document.indexing_method === 'vision-pdf-rag') {
      fetchImagePaths(document.index_id);
    } else {
      setError('Invalid document type or missing indexing method');
    }
  }, [document]);

  const fetchImagePaths = async (indexId) => {
    try {
      const response = await axios.get(`http://localhost:8000/multimodal_rag/get_image_paths/${indexId}`);
      const imagePaths = response.data.image_paths;
      setPages(imagePaths);
      await preloadImages(imagePaths);
      setImagesLoaded(true);
    } catch (error) {
      console.error('Error fetching image paths:', error);
      setError('Failed to fetch image paths');
    }
  };

  const preloadImages = (imagePaths) => {
    return Promise.all(imagePaths.map(path => {
      return new Promise((resolve, reject) => {
        const img = new Image();
        img.onload = resolve;
        img.onerror = reject;
        img.src = path;
      });
    }));
  };

  const handleImageError = (event) => {
    console.error('Image failed to load:', event.target.src);
    event.target.src = 'path/to/fallback/image.png'; // Replace with an actual fallback image
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (inputMessage.trim() === '') return;

    setIsWaitingForResponse(true);

    try {
      const response = await axios.post(
        `http://localhost:8000/multimodal_rag/query_vector_db`,
        {
          query: inputMessage,
          index_id: document.index_id,
          top_k: 1
        },
        {
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          }
        }
      );

      const { selected_page } = response.data;
      setSelectedPage(selected_page);
    } catch (error) {
      console.error('Error querying document:', error);
      setError('Unable to process your query.');
    } finally {
      setIsWaitingForResponse(false);
      setInputMessage('');
    }
  };

  useEffect(() => {
    if (imagesLoaded && selectedPage !== null && pageRefs.current[selectedPage]) {
      pageRefs.current[selectedPage].scrollIntoView({ behavior: "smooth" });
    }
  }, [selectedPage, imagesLoaded]);

  return (
    <div className="flex flex-col h-full relative">
      <div className="bg-white border-b border-gray-300">
        <form onSubmit={handleSendMessage} className="flex items-center p-2">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            placeholder="Ask a question..."
            className="flex-grow px-3 py-1 text-sm border border-gray-300 rounded-l-md focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
          <button
            type="submit"
            className="bg-blue-500 text-white px-3 py-1 text-sm rounded-r-md hover:bg-blue-600 transition duration-300 ease-in-out"
            disabled={isWaitingForResponse}
          >
            {isWaitingForResponse ? 'Searching...' : 'Search'}
          </button>
        </form>
      </div>
      <div className="flex-grow overflow-y-auto p-4">
        {error ? (
          <p className="text-red-500">{error}</p>
        ) : !imagesLoaded ? (
          <p>Loading images...</p>
        ) : (
          <div className="max-w-3xl mx-auto"> {/* Added container with max width */}
            {pages.map((page, index) => (
              <div 
                key={index}
                className="mb-4 shadow-md"
                ref={el => pageRefs.current[index] = el}
              >
                <img 
                  src={page} 
                  alt={`Page ${index + 1}`} 
                  className={`w-full border border-gray-200 rounded ${selectedPage === index ? 'border-blue-500 border-4' : ''}`}
                  onError={handleImageError}
                />
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default PDFViewer;
