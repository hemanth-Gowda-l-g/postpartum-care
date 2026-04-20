import React, { useState, useEffect } from 'react';
import axios from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip } from 'recharts';

export default function MLDashboard() {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    axios.get('/api/ml/dashboard/stats', {
      headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
    }).then(res => setStats(res.data));
  }, []);

  return (
    <div className="ml-dashboard">
      <h2>ML Model Dashboard</h2>
      
      {stats ? (
        <>
          <div className="stats-card">
            <h3>Dataset Overview</h3>
            <p>Total Records: {stats.dataset_stats.size}</p>
            <p>PPD Positive Cases: {stats.dataset_stats.ppd_positive_percentage.toFixed(1)}%</p>
          </div>

          <BarChart width={500} height={300} data={[
            { name: 'PPD Risk', value: stats.dataset_stats.ppd_positive_percentage },
            { name: 'Healthy', value: 100 - stats.dataset_stats.ppd_positive_percentage }
          ]}>
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="value" fill="#8884d8" />
          </BarChart>
        </>
      ) : (
        <p>Loading ML statistics...</p>
      )}
    </div>
  );
}