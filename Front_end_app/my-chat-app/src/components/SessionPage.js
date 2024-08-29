import React, { useState } from 'react';
import axios from 'axios';
import './SessionPage.css';

const SessionPage = () => {
  const [apiKey, setApiKey] = useState('');
  const [pdfFiles, setPdfFiles] = useState(['']);
  const [statusMessage, setStatusMessage] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);

  const handleApiKeySubmit = async () => {
    try {
      const response = await axios.post('/api/store-api-key', { apiKey });
      setStatusMessage('Stored for the session');
    } catch (error) {
      console.error('Error storing API key', error);
    }
  };

  const handlePdfUpload = (index, e) => {
    const files = [...pdfFiles];
    files[index] = e.target.files[0];
    setPdfFiles(files);
  };

  const handleAddFile = () => {
    setPdfFiles([...pdfFiles, '']);
  };

  const handlePdfSubmit = async () => {
    setIsProcessing(true);
    try {
      const formData = new FormData();
      pdfFiles.forEach((file, index) => {
        if (file) {
          formData.append(`pdfs[${index}]`, file);
        }
      });

      await axios.post('/api/upload-pdfs', formData);
      setStatusMessage('Upload complete, you can now chat with this PDF');
    } catch (error) {
      console.error('Error uploading PDFs', error);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="session-container">
      <div className="sidebar">
        <h3>Session Sidebar</h3>
        
        <div className="step">
          <h4>1. Add OpenAI Key</h4>
          <input
            type="text"
            placeholder="OpenAI API Key"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
          />
          <button onClick={handleApiKeySubmit}>Submit API Key</button>
        </div>

        <div className="step">
          <h4>2. Upload PDF Documents</h4>
          {pdfFiles.map((file, index) => (
            <input
              key={index}
              type="file"
              accept="application/pdf"
              onChange={(e) => handlePdfUpload(index, e)}
            />
          ))}
          <button onClick={handleAddFile}>Add More</button>
          <button onClick={handlePdfSubmit}>Submit PDFs</button>
        </div>

        {statusMessage && <p>{statusMessage}</p>}
        {isProcessing && <p>Processing...</p>}
      </div>
      
      <div className="chatbox">
        <h3>Chat with the PDF</h3>
        <div className="chat-window">
          {/* Messages will appear here */}
        </div>
        <div className="chat-input">
          <input type="text" placeholder="Type your message here..." />
          <button>Send</button>
        </div>
      </div>
    </div>
  );
};

export default SessionPage;
