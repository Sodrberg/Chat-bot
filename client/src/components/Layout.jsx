import React from 'react';

function Layout({ children }) {
  return (
    <div className="flex flex-col h-screen bg-gray-100 font-sans">
      <header className="bg-indigo-700 shadow-md p-4">
        <h1 className="text-2xl font-semibold text-white">AI Chat Assistant</h1>
      </header>
      <main className="flex-grow overflow-hidden">
        {children}
      </main>
      <footer className="bg-indigo-700 p-4 text-center text-sm text-white">
        <p>&copy; 2023 AI Chat Assistant. All rights reserved.</p>
      </footer>
    </div>
  );
}

export default Layout;