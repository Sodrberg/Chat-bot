import React, { useState } from 'react';
import Dashboard from './components/Dashboard';
import Sidebar from './components/Sidebar';
import Login from './components/Login'; // New import
import axios from 'axios'; // Make sure to install axios: npm install axios
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import ChatContainer from './components/ChatContainer';

function App() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [selectedStrategy, setSelectedStrategy] = useState(null);
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [showUpload, setShowUpload] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false); // New state
  const [token, setToken] = useState(null);
  const [sidebarRefreshTrigger, setSidebarRefreshTrigger] = useState(0);

  const toggleSidebar = () => {
    setIsSidebarOpen(!isSidebarOpen);
  };

  const handleLogin = async (username, password) => {
    try {
      const response = await axios.post('http://127.0.0.1:8000/auth/login', 
        new URLSearchParams({
          'username': username,
          'password': password,
        }),
        {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
          }
        }
      );
      const newToken = response.data.access_token;
      setToken(newToken);
      setIsAuthenticated(true);
    } catch (error) {
      alert('Login failed: ' + (error.response?.data?.detail || 'Unknown error'));
    }
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
    setToken(null);
    // You might want to clear any other user-related state here
  };

  const triggerSidebarRefresh = () => {
    setSidebarRefreshTrigger(prev => prev + 1);
  };

  if (!isAuthenticated) {
    return <Login onLogin={handleLogin} />;
  }

  return (
    <Router>
      <Routes>
        <Route path="/chat/:indexId" element={<ChatContainer />} />
        <Route path="/" element={
          <div className="App flex">
            <Sidebar 
              isOpen={isSidebarOpen} 
              selectedStrategy={selectedStrategy}
              setSelectedStrategy={setSelectedStrategy}
              selectedDocument={selectedDocument}
              setSelectedDocument={setSelectedDocument}
              setShowUpload={setShowUpload}
              token={token}
              refreshTrigger={sidebarRefreshTrigger}
            />
            <div className={`flex-1 transition-margin duration-300 ease-in-out ${isSidebarOpen ? 'ml-64' : 'ml-0'}`}>
              <div className="fixed top-4 left-4 z-30 flex space-x-2">
                <button
                  onClick={toggleSidebar}
                  className="bg-blue-500 text-white p-2 rounded-md"
                >
                  {isSidebarOpen ? 'Close Menu' : 'Open Menu'}
                </button>
                <button
                  onClick={handleLogout}
                  className="bg-red-500 text-white p-2 rounded-md"
                >
                  Logout
                </button>
              </div>
              <Dashboard 
                selectedStrategy={selectedStrategy} 
                selectedDocument={selectedDocument}
                showUpload={showUpload}
                setShowUpload={setShowUpload}
                token={token}
                triggerSidebarRefresh={triggerSidebarRefresh}
              />
            </div>
          </div>
        } />
      </Routes>
    </Router>
  );
}

export default App;