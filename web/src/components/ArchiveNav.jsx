import React, { useState, useEffect } from 'react';

const ArchiveNav = ({ selectedDate, setSelectedDate }) => {
  const [archiveDates, setArchiveDates] = useState([]);

  useEffect(() => {
    const fetchArchiveIndex = async () => {
      try {
        const baseUrl = import.meta.env.BASE_URL || '/';
        const res = await fetch(`${baseUrl}data/archive/index.json`);
        if (res.ok) {
          const json = await res.json();
          if (json.dates && Array.isArray(json.dates)) {
            setArchiveDates(json.dates);
          }
        }
      } catch (err) {
        // Silently fail, archive might not exist yet
        console.log("No archive index found yet.");
      }
    };
    fetchArchiveIndex();
  }, []);

  if (archiveDates.length === 0) return null;

  return (
    <div className="archive-nav">
      <h2 className="section-title" style={{ fontSize: '1.2rem', marginBottom: '16px' }}>
        <span>📅 Past Reports</span>
        <div className="title-underline" style={{ opacity: 0.5 }}></div>
      </h2>
      
      <div className="archive-list">
        <button 
          className={`archive-pill ${!selectedDate ? 'active' : ''}`}
          onClick={() => setSelectedDate(null)}
        >
          Latest
        </button>
        
        {archiveDates.slice(0, 5).map(dateStr => (
          <button 
            key={dateStr}
            className={`archive-pill ${selectedDate === dateStr ? 'active' : ''}`}
            onClick={() => setSelectedDate(dateStr)}
          >
            {dateStr}
          </button>
        ))}
      </div>
    </div>
  );
};

export default ArchiveNav;
