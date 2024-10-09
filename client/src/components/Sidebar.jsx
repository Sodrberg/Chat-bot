import React, { useState, useEffect } from 'react';
import axios from 'axios';

const strategies = [
  { id: 'llamaparse', name: 'LlamaParse' },
  { id: 'graphrag', name: 'GraphRAG' },
  { id: 'vision-pdf-rag', name: 'Vision-PDF-RAG' }, // Add the new strategy
  { id: 'other_strategy', name: 'Other Strategy' },
];

// This would typically come from an API or state management
const documents = [
  { id: 'doc1', name: 'Document 1 (LlamaParse)', strategy: 'llamaparse' },
  { id: 'doc2', name: 'Document 2 (LlamaParse)', strategy: 'llamaparse' },
  { id: 'doc3', name: 'Document 3 (GraphRAG)', strategy: 'graphrag' },
  { id: 'doc4', name: 'Document 4 (GraphRAG)', strategy: 'graphrag' },
  { id: 'doc5', name: 'Document 5 (Other)', strategy: 'other_strategy' },
];

function Sidebar({ isOpen, selectedStrategy, setSelectedStrategy, selectedDocument, setSelectedDocument, setShowUpload, token, refreshTrigger }) {
  const [showStrategies, setShowStrategies] = useState(false);
  const [indexedDocuments, setIndexedDocuments] = useState([]);

  useEffect(() => {
    fetchIndexedDocuments();
  }, [token, refreshTrigger]);

  const fetchIndexedDocuments = async () => {
    try {
      const response = await axios.get('http://127.0.0.1:8000/indexed-documents', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      setIndexedDocuments(response.data);
      console.log(response.data);  // Add this line to check the fetched data
    } catch (error) {
      console.error('Error fetching indexed documents:', error);
    }
  };

  const handleUploadClick = () => {
    setShowStrategies(true);
    setSelectedStrategy(null);
    setShowUpload(false);
  };

  const handleStrategySelect = (strategyId) => {
    setSelectedStrategy(strategyId);
    setShowUpload(true);
  };

  return (
    <div className={`fixed inset-y-0 left-0 w-64 bg-gray-800 text-white transform ${isOpen ? 'translate-x-0' : '-translate-x-full'} transition-transform duration-300 ease-in-out overflow-y-auto`}>
      <div className="p-4 pt-16">
        <button
          onClick={handleUploadClick}
          className="w-full bg-yellow-500 hover:bg-yellow-600 text-gray-800 font-bold py-2 px-4 rounded mb-8"
        >
          Upload New Document
        </button>
        
        {showStrategies && (
          <>
            <p className="text-sm mb-2">Choose a RAG strategy to index a new document:</p>
            <ul className="mb-8">
              {strategies.map((strategy) => (
                <li key={strategy.id} className="mb-2">
                  <button
                    onClick={() => handleStrategySelect(strategy.id)}
                    className={`w-full text-left py-2 px-4 rounded ${
                      selectedStrategy === strategy.id
                        ? 'bg-blue-500 text-white'
                        : 'hover:bg-gray-700'
                    }`}
                  >
                    {strategy.name}
                  </button>
                </li>
              ))}
            </ul>
          </>
        )}

        <h2 className="text-2xl font-semibold mb-4">Indexed Documents</h2>
        <ul>
          {indexedDocuments.map((doc) => (
            <li key={doc.id} className="mb-2">
              <button
                onClick={() => {
                  setSelectedDocument({
                    id: doc.id,
                    document_name: doc.document_name,
                    index_id: doc.index_id,
                    indexing_method: doc.indexing_method
                  });
                  setSelectedStrategy(doc.indexing_method);
                  setShowStrategies(false);
                  setShowUpload(false);
                  // Remove the setInitialViewMode call
                }}
                className={`w-full text-left py-2 px-4 rounded ${
                  selectedDocument?.id === doc.id
                    ? 'bg-green-500 text-white'
                    : 'hover:bg-gray-700'
                }`}
              >
                <div>{doc.document_name}</div>
                <div className={`text-xs ${
                  selectedDocument?.id === doc.id
                    ? 'text-green-200'
                    : 'text-gray-400'
                }`}>
                  {strategies.find(s => s.id === doc.indexing_method)?.name || doc.indexing_method}
                </div>
              </button>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

export default Sidebar;