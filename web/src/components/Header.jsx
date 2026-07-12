import React, { useState, useEffect } from 'react';

const Header = ({ date, generatedAt }) => {
  const [relativeTime, setRelativeTime] = useState('');

  useEffect(() => {
    if (!generatedAt) return;
    
    const updateRelativeTime = () => {
      const genTime = new Date(generatedAt);
      const now = new Date();
      const diffMs = now - genTime;
      const diffHrs = Math.floor(diffMs / (1000 * 60 * 60));
      const diffMins = Math.floor(diffMs / (1000 * 60));
      
      if (diffHrs > 0) {
        setRelativeTime(`Updated ${diffHrs} hour${diffHrs > 1 ? 's' : ''} ago`);
      } else if (diffMins > 0) {
        setRelativeTime(`Updated ${diffMins} min${diffMins > 1 ? 's' : ''} ago`);
      } else {
        setRelativeTime('Updated just now');
      }
    };

    updateRelativeTime();
    const interval = setInterval(updateRelativeTime, 60000); // update every min
    return () => clearInterval(interval);
  }, [generatedAt]);

  const formattedDate = new Date(date).toLocaleDateString('en-US', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric'
  });

  return (
    <header className="header-hero">
      <div className="header-bg-orbs">
        <div className="orb orb-1"></div>
        <div className="orb orb-2"></div>
      </div>
      
      <h1 className="text-gradient">Market Intelligence</h1>
      <p>AI-Powered Stock & Commodity Insights</p>
      
      <div className="header-date font-mono">
        <span>{formattedDate}</span>
        <span style={{ margin: '0 10px', opacity: 0.5 }}>|</span>
        <span style={{ color: 'var(--accent-cyan)' }}>{relativeTime}</span>
      </div>
    </header>
  );
};

export default Header;
