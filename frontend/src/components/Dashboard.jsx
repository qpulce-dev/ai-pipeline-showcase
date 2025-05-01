import React, { useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { BookOpen, Database, Server, Search } from 'lucide-react';

// Mock data for demonstration
const initialData = [
  { category: 'Electronics', count: 35, avgRating: 4.2 },
  { category: 'Clothing', count: 28, avgRating: 3.8 },
  { category: 'Home', count: 22, avgRating: 4.0 },
  { category: 'Books', count: 18, avgRating: 4.5 },
  { category: 'Food', count: 12, avgRating: 3.9 }
];

const statusCards = [
  { title: 'ETL Status', icon: <Database size={24} />, status: 'Healthy', lastRun: '10 minutes ago', color: 'bg-green-100' },
  { title: 'Vector Store', icon: <BookOpen size={24} />, status: 'Healthy', lastRun: '10 minutes ago', color: 'bg-green-100' },
  { title: 'API Service', icon: <Server size={24} />, status: 'Healthy', lastRun: 'Now', color: 'bg-green-100' },
  { title: 'LLM Service', icon: <Search size={24} />, status: 'Healthy', lastRun: '2 minutes ago', color: 'bg-green-100' }
];

const AIPipelineDashboard = () => {
  const [data] = useState(initialData);
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = () => {
    if (!question.trim()) return;

    setLoading(true);

    // Simulate API call
    setTimeout(() => {
      setAnswer(`Based on our product database, ${question.includes('electronics') ?
        'the top-rated electronics are smartphones with an average rating of 4.5 stars. The most common positive feedback mentions camera quality and battery life.' :
        'we found several relevant products. The highest rated items have excellent customer reviews, with most customers mentioning quality and value as key factors.'}`);
      setLoading(false);
    }, 1500);
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-800 mb-6">AI Pipeline Dashboard</h1>

        {/* Status Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {statusCards.map((card, index) => (
            <div key={index} className={`${card.color} p-4 rounded-lg shadow-sm`}>
              <div className="flex items-center mb-2">
                {card.icon}
                <h3 className="text-lg font-semibold ml-2">{card.title}</h3>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-green-800 font-medium">{card.status}</span>
                <span className="text-sm text-gray-600">Last run: {card.lastRun}</span>
              </div>
            </div>
          ))}
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Data Visualization */}
          <div className="bg-white p-6 rounded-lg shadow-sm">
            <h2 className="text-xl font-semibold mb-4">Product Categories</h2>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={data}
                  margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="category" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="count" fill="#8884d8" name="Number of Products" />
                  <Bar dataKey="avgRating" fill="#82ca9d" name="Average Rating" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* RAG Interface */}
          <div className="bg-white p-6 rounded-lg shadow-sm">
            <h2 className="text-xl font-semibold mb-4">Product AI Assistant</h2>
            <div>
              <div className="mb-4">
                <label className="block text-gray-700 mb-2">Ask a question about our products:</label>
                <input
                  type="text"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  className="w-full p-2 border border-gray-300 rounded"
                  placeholder="E.g., What are the best electronics products?"
                />
              </div>
              <button
                onClick={handleSubmit}
                className="bg-blue-500 text-white py-2 px-4 rounded hover:bg-blue-600 transition"
                disabled={loading}
              >
                {loading ? 'Processing...' : 'Ask Question'}
              </button>
            </div>

            {answer && (
              <div className="mt-4 p-4 bg-gray-50 rounded">
                <h3 className="font-medium mb-2">Answer:</h3>
                <p className="text-gray-700">{answer}</p>
              </div>
            )}
          </div>
        </div>

        {/* Recent Activity */}
        <div className="mt-8 bg-white p-6 rounded-lg shadow-sm">
          <h2 className="text-xl font-semibold mb-4">Recent Activity</h2>
          <table className="min-w-full">
            <thead>
              <tr className="bg-gray-50">
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Timestamp</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Activity</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              <tr>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">Today, 10:30 AM</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">ETL Pipeline Execution</td>
                <td className="px-6 py-4 whitespace-nowrap"><span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">Completed</span></td>
              </tr>
              <tr>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">Today, 10:32 AM</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">Vector Store Update</td>
                <td className="px-6 py-4 whitespace-nowrap"><span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">Completed</span></td>
              </tr>
              <tr>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">Today, 09:15 AM</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">RAG Query: "Best electronics"</td>
                <td className="px-6 py-4 whitespace-nowrap"><span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">Completed</span></td>
              </tr>
              <tr>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">Yesterday, 04:20 PM</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">System Health Check</td>
                <td className="px-6 py-4 whitespace-nowrap"><span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">Passed</span></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default AIPipelineDashboard;
