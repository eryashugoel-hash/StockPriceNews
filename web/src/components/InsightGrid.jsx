import React from 'react';
import InsightCard from './InsightCard';

const InsightGrid = ({ insights }) => {
  if (!insights || insights.length === 0) {
    return (
      <div className="empty-state" style={{ padding: '40px 20px', marginTop: '20px' }}>
        <p className="empty-sub">No insights match the current filter.</p>
      </div>
    );
  }

  return (
    <div className="insight-grid">
      {insights.map((insight, index) => (
        <InsightCard 
          key={`${insight.headline}-${index}`} 
          insight={insight} 
          index={index} 
        />
      ))}
    </div>
  );
};

export default InsightGrid;
