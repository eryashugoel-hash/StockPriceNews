import React, { useEffect, useRef } from 'react';

const InsightCard = ({ insight, index }) => {
  const barRef = useRef(null);

  useEffect(() => {
    // Simple intersection observer to trigger the bar fill animation
    // when the card scrolls into view
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting && barRef.current) {
          barRef.current.style.setProperty('--target-width', `${Math.round(insight.confidence * 100)}%`);
          barRef.current.classList.add('conf-bar-fill');
        }
      });
    }, { threshold: 0.1 });

    if (barRef.current) observer.observe(barRef.current);
    
    return () => observer.disconnect();
  }, [insight.confidence]);

  const sentimentData = {
    bullish: { icon: '▲', label: 'Bullish', class: 'bullish' },
    bearish: { icon: '▼', label: 'Bearish', class: 'bearish' },
    neutral: { icon: '●', label: 'Neutral', class: 'neutral' }
  }[insight.sentiment] || { icon: '●', label: 'Unknown', class: 'neutral' };

  const actionData = {
    watch: { label: '👀 Watch', class: 'act-watch' },
    buy_opportunity: { label: '🟢 Buy Opportunity', class: 'act-buy' },
    risk_alert: { label: '🔴 Risk Alert', class: 'act-risk' }
  }[insight.action] || { label: insight.action, class: 'act-watch' };

  return (
    <div 
      className="glass-card insight-card" 
      style={{ animationDelay: `${index * 0.1}s` }}
    >
      <div className={`card-accent-border card-accent-${sentimentData.class}`}></div>
      
      <div className="card-header">
        <div className="rank-badge">#{insight.rank}</div>
        <div className="badges-right">
          <span className="chip chip-category">{insight.category.replace('_', ' ')}</span>
          <span className="chip chip-source">{insight.source}</span>
        </div>
      </div>

      <h3 className="card-title">{insight.headline}</h3>

      <div className="asset-chips">
        {insight.affected_assets.map(asset => (
          <span key={asset} className={`asset-chip asset-${insight.asset_type}`}>
            {asset}
          </span>
        ))}
      </div>

      <div className="sentiment-row">
        <div className={`sentiment-indicator sent-${sentimentData.class}`}>
          {sentimentData.icon} {sentimentData.label}
        </div>
        
        <div className="confidence-meter">
          <div className="conf-header font-mono">
            <span>Confidence</span>
            <span>{Math.round(insight.confidence * 100)}%</span>
          </div>
          <div className="conf-bar-bg">
            <div 
              ref={barRef}
              className={`conf-fill-${sentimentData.class}`} 
            ></div>
          </div>
        </div>
      </div>

      <p className="card-reasoning">{insight.reasoning}</p>

      <div className="card-footer">
        <a href={insight.source_url} target="_blank" rel="noopener noreferrer" className="source-link">
          Read source →
        </a>
        <div className={`action-badge ${actionData.class}`}>
          {actionData.label}
        </div>
      </div>
    </div>
  );
};

export default InsightCard;
