import React from 'react';

const TweetSection = ({ tweets }) => {
  if (!tweets || tweets.length === 0) return null;

  return (
    <div style={{ marginTop: '20px' }}>
      <h2 className="section-title">
        <span>🐦 Trending from Influential Voices</span>
        <div className="title-underline"></div>
      </h2>
      
      <div className="tweet-scroll">
        {tweets.map((tweet, index) => {
          const initial = tweet.author ? tweet.author.charAt(0) : 'T';
          
          return (
            <div key={index} className="glass-card tweet-card">
              <div className="tweet-header">
                <div className="tweet-avatar">{initial}</div>
                <div className="tweet-author">
                  <span className="t-name">{tweet.author}</span>
                  <span className="t-handle font-mono">{tweet.handle}</span>
                </div>
              </div>
              
              <p className="tweet-text">"{tweet.text}"</p>
              
              <div className="tweet-footer">
                <span className="t-relevance">{tweet.relevance}</span>
                <span className="t-time font-mono">
                  {new Date(tweet.timestamp).toLocaleDateString()}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default TweetSection;
