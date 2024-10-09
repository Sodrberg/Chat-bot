import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import PDFViewer from './PDFViewer';
import { useParams } from 'react-router-dom';

function ChatContainer({ strategy, document, token }) {
  const [conversations, setConversations] = useState({});
  const [inputMessage, setInputMessage] = useState('');
  const [isWaitingForResponse, setIsWaitingForResponse] = useState(false);
  const messagesEndRef = useRef(null);
  const [isGlobalSearch, setIsGlobalSearch] = useState(true);
  const [viewMode, setViewMode] = useState('chat');

  useEffect(() => {
    // Set the initial view mode when the document changes
    setViewMode(strategy === 'vision-pdf-rag' ? 'pdf' : 'chat');
  }, [strategy, document]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }

  useEffect(() => {
    scrollToBottom();
  }, [conversations]);

  const getCurrentConversation = () => {
    const key = `${strategy}-${document.index_id}`;
    return conversations[key] || [];
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (inputMessage.trim() === '') return;

    const key = `${strategy}-${document.index_id}`;
    const updatedConversation = [...getCurrentConversation(), { text: inputMessage, sender: 'user' }];
    
    setConversations(prev => ({
      ...prev,
      [key]: updatedConversation
    }));
    setInputMessage('');
    setIsWaitingForResponse(true);

    try {
      let response;
      console.log('Strategy:', strategy);
      console.log('Document:', document);

      if (strategy === 'llamaparse') {
        console.log('Sending llamaparse query with:', { query: inputMessage, index_id: document.index_id });

        response = await axios.post(`http://127.0.0.1:8000/llamaparse/query`, 
          { Query: inputMessage, Index_id: document.index_id },
          {
            headers: { 
              'Content-Type': 'application/json',
            }
          }
        );
      } else if (strategy === 'GraphRAG') {
        console.log('Sending GraphRAG query with:', { query: inputMessage, Index_id: document.index_id, isGlobalSearch });
        const endpoint = isGlobalSearch ? '/graphrag/global_search' : '/graphrag/local_search';
        response = await axios.post(`http://127.0.0.1:8000${endpoint}`, 
          { Query: inputMessage, Index_id: document.index_id },
          {
            headers: { 
              'Content-Type': 'application/json',
            }
          }
        );
      } else if (strategy === 'vision-pdf-rag') {
        console.log('Sending vision-pdf-rag query with:', { query: inputMessage, index_id: document.index_id });
        response = await axios.post(`http://127.0.0.1:8000/multimodal_rag/query_vector_db`, 
          { 
            query: inputMessage, 
            index_id: document.index_id,
            top_k: 5
          },
          {
            headers: { 
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`
            }
          }
        );
      } else {
        throw new Error(`Unsupported strategy: ${strategy}`);
      }

      console.log('Response:', response);

      if (response && response.data) {
        let aiResponse;
        if (strategy === 'vision-pdf-rag') {
          const { results, selected_page } = response.data;
          aiResponse = `Selected page: ${selected_page}\n\n`;
          aiResponse += results.map(result => 
            `Page content: ${result.page_content}\nMetadata: ${JSON.stringify(result.metadata)}`
          ).join('\n\n');
        } else {
          aiResponse = response.data.message;
        }

        setConversations(prev => ({
          ...prev,
          [key]: [...updatedConversation, { text: aiResponse, sender: 'ai' }]
        }));
      } else {
        throw new Error('Response or response.data is undefined');
      }
    } catch (error) {
      console.error('Error querying document:', error);
      console.error('Error details:', error.response ? error.response.data : 'No response data');
      setConversations(prev => ({
        ...prev,
        [key]: [...updatedConversation, { text: `Error: ${error.message || 'Unable to process your query.'}`, sender: 'ai' }]
      }));
    } finally {
      setIsWaitingForResponse(false);
    }
  };

  useEffect(() => {
    console.log('ViewMode:', viewMode);
    console.log('Document:', document);
  }, [viewMode, document]);

  const handleToggleSearch = () => {
    setIsGlobalSearch(!isGlobalSearch);
  };

  return (
    <div className="flex flex-col h-full bg-white relative">
      <div className="flex-grow flex flex-col overflow-hidden">
        <div className="bg-gray-100 py-1 px-2 flex justify-between items-center shadow-md">
          <h2 className="text-base font-semibold">Chatting with: {document.document_name} ({strategy})</h2>
          {strategy === 'vision-pdf-rag' && (
            <div className="flex items-center">
              <button
                onClick={() => setViewMode(viewMode === 'chat' ? 'pdf' : 'chat')}
                className="ml-2 bg-blue-500 text-white px-2 py-1 text-sm rounded hover:bg-blue-600"
              >
                {viewMode === 'chat' ? 'View PDF' : 'Back to Chat'}
              </button>
            </div>
          )}
          {strategy === 'GraphRAG' && (
            <div className="flex items-center space-x-2">
              <span className="text-xs font-medium text-gray-700">
                {isGlobalSearch ? 'Global' : 'Local'} Search
              </span>
              <label className="inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  className="sr-only peer"
                  checked={isGlobalSearch}
                  onChange={handleToggleSearch}
                />
                <div className="relative w-9 h-5 bg-gray-200 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-blue-300 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
              </label>
            </div>
          )}
        </div>
        <div className="flex-grow flex overflow-hidden">
          {strategy === 'vision-pdf-rag' && viewMode === 'pdf' ? (
            <div className="flex-grow overflow-hidden">
              <PDFViewer document={document} token={token} />
            </div>
          ) : (
            <div className="flex-grow flex flex-col overflow-hidden">
              <div className="flex-grow overflow-y-auto p-2 space-y-2">
                {getCurrentConversation().map((message, index) => (
                  <div key={index} className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-xs md:max-w-md lg:max-w-lg xl:max-w-xl rounded-lg p-3 ${message.sender === 'user' ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-800'}`}>
                      <span className="block font-bold mb-1">{message.sender === 'user' ? 'You' : 'AI'}</span>
                      <p>{message.text}</p>
                    </div>
                  </div>
                ))}
                {isWaitingForResponse && (
                  <div className="flex justify-start">
                    <div className="bg-gray-100 text-gray-800 rounded-lg p-3">
                      <span className="block font-bold mb-1">AI</span>
                      <div className="flex items-center">
                        <div className="mr-2 w-5 h-5 border-t-2 border-b-2 border-blue-500 rounded-full animate-spin"></div>
                        Thinking...
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
              <form onSubmit={handleSendMessage} className="border-t border-gray-200 p-2">
                <div className="flex space-x-2">
                  <input
                    type="text"
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    placeholder="Type your message..."
                    className="flex-grow border border-gray-300 rounded-full px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <button 
                    type="submit" 
                    className="bg-blue-500 text-white rounded-full px-4 py-2 hover:bg-blue-600 transition duration-300 ease-in-out"
                    disabled={isWaitingForResponse}
                  >
                    Send
                  </button>
                </div>
              </form>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default ChatContainer;