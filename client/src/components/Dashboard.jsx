import React, { useState } from 'react';
import ChatContainer from './ChatContainer';
import FileUpload from './FileUpload';

function Dashboard({ selectedStrategy, selectedDocument, showUpload, setShowUpload, token, triggerSidebarRefresh }) {
  const handleUploadComplete = (uploadedDocument) => {
    console.log('Document uploaded:', uploadedDocument);
    setShowUpload(false);
    triggerSidebarRefresh();
  };

  return (
    <div className="flex flex-col h-screen">
      <div className="flex-grow p-4 pt-16 overflow-hidden">
        {showUpload ? (
          <FileUpload strategy={selectedStrategy} onUploadComplete={handleUploadComplete} token={token} />
        ) : selectedStrategy && selectedDocument ? (
          <div className="h-full overflow-hidden flex flex-col">
            <div className="flex-shrink-0">
              {/* This div will contain the fixed header from ChatContainer */}
            </div>
            <div className="flex-grow overflow-auto">
              <ChatContainer strategy={selectedStrategy} document={selectedDocument} token={token} />
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-center h-full">
            <p className="text-xl text-gray-500 text-center px-4">
              {!selectedStrategy
                ? "Select a document or upload a new one in the sidebar"
                : !selectedDocument
                ? "Select an indexed document from the sidebar or index a new document"
                : "An unexpected error occurred"}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

export default Dashboard;