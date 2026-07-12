import React from 'react';

const LoadingSkeleton = () => {
  return (
    <div>
      {/* Pulse skeleton */}
      <div className="market-pulse-wrapper">
        <div className="glass-card skel-pulse">
          <div className="skeleton-bg skel-pulse-item"></div>
          <div className="skeleton-bg skel-pulse-item"></div>
          <div className="skeleton-bg skel-pulse-item"></div>
        </div>
      </div>
      
      {/* Grid skeletons */}
      <div className="insight-grid">
        {[1, 2, 3, 4].map(i => (
          <div key={i} className="glass-card insight-card skel-card">
            <div className="card-header">
              <div className="skeleton-bg" style={{width: 32, height: 32, borderRadius: '50%'}}></div>
              <div className="badges-right">
                <div className="skeleton-bg skel-chip"></div>
                <div className="skeleton-bg skel-chip"></div>
              </div>
            </div>
            
            <div className="skeleton-bg skel-title" style={{marginTop: 16}}></div>
            <div className="skeleton-bg skel-title" style={{width: '50%'}}></div>
            
            <div style={{display: 'flex', gap: 8, marginTop: 8}}>
              <div className="skeleton-bg skel-chip"></div>
            </div>
            
            <div className="sentiment-row">
              <div className="skeleton-bg skel-chip" style={{width: 90}}></div>
              <div className="skeleton-bg" style={{flex: 1, height: 6, borderRadius: 3}}></div>
            </div>
            
            <div style={{marginTop: 20}}>
              <div className="skeleton-bg skel-text"></div>
              <div className="skeleton-bg skel-text"></div>
              <div className="skeleton-bg skel-text" style={{width: '80%'}}></div>
            </div>
            
            <div className="card-footer">
              <div className="skeleton-bg skel-text" style={{width: 80, margin: 0}}></div>
              <div className="skeleton-bg skel-chip" style={{width: 120}}></div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default LoadingSkeleton;
