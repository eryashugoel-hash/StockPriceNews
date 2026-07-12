import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import MarketPulse from './components/MarketPulse';
import FilterBar from './components/FilterBar';
import InsightGrid from './components/InsightGrid';
import TweetSection from './components/TweetSection';
import ArchiveNav from './components/ArchiveNav';
import Footer from './components/Footer';
import LoadingSkeleton from './components/LoadingSkeleton';
import EmptyState from './components/EmptyState';

function App() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('all');
  const [selectedDate, setSelectedDate] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      
      const baseUrl = import.meta.env.BASE_URL || '/';
      let url = `${baseUrl}data/latest.json`;
      
      if (selectedDate) {
        url = `${baseUrl}data/archive/${selectedDate}.json`;
      }

      try {
        // In local development, if fetching archive fails, don't crash
        const res = await fetch(url);
        if (!res.ok) {
           if(selectedDate) {
               throw new Error(`Data for ${selectedDate} not found.`);
           } else {
               throw new Error('Latest data not available yet.');
           }
        }
        const json = await res.json();
        setData(json);
      } catch (err) {
        console.error("Error fetching data:", err);
        setError(err.message);
        setData(null);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [selectedDate]);

  let filteredInsights = [];
  if (data && data.insights) {
    if (filter === 'all') {
      filteredInsights = data.insights;
    } else {
      filteredInsights = data.insights.filter(i => i.sentiment === filter);
    }
  }

  return (
    <div className="app-container">
      {data && <Header date={data.date} generatedAt={data.generated_at} />}
      
      <main className="container">
        {loading ? (
          <LoadingSkeleton />
        ) : error ? (
          <EmptyState message={error} />
        ) : data ? (
          <>
            <MarketPulse pulse={data.market_pulse} />
            <FilterBar filter={filter} setFilter={setFilter} insights={data.insights} />
            <InsightGrid insights={filteredInsights} />
            {data.tweets && data.tweets.length > 0 && <TweetSection tweets={data.tweets} />}
          </>
        ) : (
           <EmptyState message="No data available" />
        )}

        <ArchiveNav selectedDate={selectedDate} setSelectedDate={setSelectedDate} />
      </main>
      
      <Footer />
    </div>
  );
}

export default App;
