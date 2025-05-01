import React, { useState, useEffect } from 'react';

function SimpleView() {
  const [status, setStatus] = useState('Loading...');
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');

  // Check API health on component mount
  useEffect(() => {
    // Replace API URL with localhost for browser access
    const apiUrl = window.location.hostname === 'localhost' ? 'http://localhost:8000' : process.env.REACT_APP_API_URL;
    console.log("Attempting to connect to API at:", apiUrl);

    fetch(`${apiUrl}/health`)
      .then(response => {
        console.log("API response received:", response.status);
        if (response.ok) {
          return response.json();
        }
        throw new Error('Network response was not ok');
      })
      .then(data => {
        console.log("API health data:", data);
        setStatus(`API Status: ${data.status}`);
      })
      .catch(error => {
        console.error('Error fetching health status:', error);
        setStatus('API Status: Not available');
      });
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();

    if (!question.trim()) return;

    fetch('http://localhost:8000/ask', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ question }),
    })
      .then(response => response.json())
      .then(data => {
        setAnswer(data.answer);
      })
      .catch(error => {
        console.error('Error asking question:', error);
        setAnswer('Error: Could not get an answer from the API');
      });
  };

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', padding: '20px' }}>
      <h1>AI Pipeline Showcase</h1>
      <div style={{ marginBottom: '20px', padding: '10px', background: '#f0f0f0', borderRadius: '5px' }}>
        {status}
      </div>

      <div style={{ marginBottom: '20px' }}>
        <h2>Ask a Question</h2>
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Enter your question here"
            style={{ padding: '10px', fontSize: '16px' }}
          />
          <button
            type="submit"
            style={{
              padding: '10px',
              background: '#0066cc',
              color: 'white',
              border: 'none',
              borderRadius: '5px',
              cursor: 'pointer'
            }}
          >
            Ask
          </button>
        </form>
      </div>

      {answer && (
        <div style={{ marginTop: '20px', padding: '15px', background: '#e6f7ff', borderRadius: '5px' }}>
          <h3>Answer:</h3>
          <p>{answer}</p>
        </div>
      )}
    </div>
  );
}

export default SimpleView;
