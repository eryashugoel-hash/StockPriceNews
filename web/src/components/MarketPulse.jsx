import React from 'react';

const MarketPulse = ({ pulse }) => {
  if (!pulse) return null;

  return (
    <div className="market-pulse-wrapper">
      <div className="glass-card market-pulse-card">
        <div className="pulse-item pulse-bullish">
          <span className="pulse-count">{pulse.bullish}</span>
          <span className="pulse-label">▲ Bullish</span>
        </div>
        <div className="pulse-item pulse-bearish">
          <span className="pulse-count">{pulse.bearish}</span>
          <span className="pulse-label">▼ Bearish</span>
        </div>
        <div className="pulse-item pulse-neutral">
          <span className="pulse-count">{pulse.neutral}</span>
          <span className="pulse-label">● Neutral</span>
        </div>
      </div>
    </div>
  );
};

export default MarketPulse;
