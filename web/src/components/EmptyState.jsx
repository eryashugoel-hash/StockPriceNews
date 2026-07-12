import React from 'react';

const EmptyState = ({ message }) => {
  return (
    <div className="empty-state">
      <div className="empty-icon">📊</div>
      <h2 className="empty-title">No Insights Available</h2>
      <p className="empty-sub">{message || "The AI agent hasn't generated the daily report yet. Check back soon."}</p>
    </div>
  );
};

export default EmptyState;
