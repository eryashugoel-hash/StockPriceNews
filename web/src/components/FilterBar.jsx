import React from 'react';

const FilterBar = ({ filter, setFilter, insights }) => {
  const counts = {
    all: insights.length,
    bullish: insights.filter(i => i.sentiment === 'bullish').length,
    bearish: insights.filter(i => i.sentiment === 'bearish').length,
    neutral: insights.filter(i => i.sentiment === 'neutral').length
  };

  return (
    <div className="filter-bar">
      <button 
        className={`filter-btn ${filter === 'all' ? 'active' : ''}`}
        onClick={() => setFilter('all')}
      >
        All Insights <span className="filter-badge">{counts.all}</span>
      </button>
      <button 
        className={`filter-btn ${filter === 'bullish' ? 'active' : ''}`}
        onClick={() => setFilter('bullish')}
      >
        ▲ Bullish <span className="filter-badge" style={{color: 'var(--bullish)'}}>{counts.bullish}</span>
      </button>
      <button 
        className={`filter-btn ${filter === 'bearish' ? 'active' : ''}`}
        onClick={() => setFilter('bearish')}
      >
        ▼ Bearish <span className="filter-badge" style={{color: 'var(--bearish)'}}>{counts.bearish}</span>
      </button>
      <button 
        className={`filter-btn ${filter === 'neutral' ? 'active' : ''}`}
        onClick={() => setFilter('neutral')}
      >
        ● Neutral <span className="filter-badge" style={{color: 'var(--neutral)'}}>{counts.neutral}</span>
      </button>
    </div>
  );
};

export default FilterBar;
