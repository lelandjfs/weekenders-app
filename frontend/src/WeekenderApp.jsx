import React, { useState, useRef, useEffect } from 'react';

const WeekenderApp = () => {
  const [activeTab, setActiveTab] = useState('search');
  const [activeCategory, setActiveCategory] = useState('all');
  const [searchCity, setSearchCity] = useState('');
  const [searchDate, setSearchDate] = useState('this-weekend');
  const [customStartDate, setCustomStartDate] = useState('');
  const [customEndDate, setCustomEndDate] = useState('');
  const [subscribeEmail, setSubscribeEmail] = useState('');
  const [subscribeCity, setSubscribeCity] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [hasResults, setHasResults] = useState(false);
  const [subscribed, setSubscribed] = useState(false);
  const [isSubscribing, setIsSubscribing] = useState(false);
  const [subscribeError, setSubscribeError] = useState('');
  const [showCitySuggestions, setShowCitySuggestions] = useState(false);
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [showSubscribeCitySuggestions, setShowSubscribeCitySuggestions] = useState(false);
  
  const cityInputRef = useRef(null);
  const datePickerRef = useRef(null);
  const subscribeCityRef = useRef(null);

  // Expanded city list - in production, connect to Google Places API or your agent's supported cities
  const cities = [
    // California
    { name: 'San Francisco', state: 'CA' },
    { name: 'Los Angeles', state: 'CA' },
    { name: 'San Diego', state: 'CA' },
    { name: 'San Jose', state: 'CA' },
    { name: 'Oakland', state: 'CA' },
    { name: 'Sacramento', state: 'CA' },
    { name: 'Santa Monica', state: 'CA' },
    { name: 'Berkeley', state: 'CA' },
    { name: 'Pasadena', state: 'CA' },
    { name: 'Long Beach', state: 'CA' },
    // New York
    { name: 'New York', state: 'NY' },
    { name: 'Brooklyn', state: 'NY' },
    { name: 'Queens', state: 'NY' },
    { name: 'Buffalo', state: 'NY' },
    { name: 'Rochester', state: 'NY' },
    // Texas
    { name: 'Austin', state: 'TX' },
    { name: 'Houston', state: 'TX' },
    { name: 'Dallas', state: 'TX' },
    { name: 'San Antonio', state: 'TX' },
    { name: 'Fort Worth', state: 'TX' },
    { name: 'El Paso', state: 'TX' },
    // Pacific Northwest
    { name: 'Seattle', state: 'WA' },
    { name: 'Portland', state: 'OR' },
    { name: 'Tacoma', state: 'WA' },
    { name: 'Spokane', state: 'WA' },
    { name: 'Eugene', state: 'OR' },
    // Mountain
    { name: 'Denver', state: 'CO' },
    { name: 'Boulder', state: 'CO' },
    { name: 'Salt Lake City', state: 'UT' },
    { name: 'Phoenix', state: 'AZ' },
    { name: 'Tucson', state: 'AZ' },
    { name: 'Albuquerque', state: 'NM' },
    { name: 'Santa Fe', state: 'NM' },
    { name: 'Las Vegas', state: 'NV' },
    { name: 'Reno', state: 'NV' },
    // Midwest
    { name: 'Chicago', state: 'IL' },
    { name: 'Minneapolis', state: 'MN' },
    { name: 'St. Paul', state: 'MN' },
    { name: 'Detroit', state: 'MI' },
    { name: 'Ann Arbor', state: 'MI' },
    { name: 'Milwaukee', state: 'WI' },
    { name: 'Madison', state: 'WI' },
    { name: 'Cleveland', state: 'OH' },
    { name: 'Columbus', state: 'OH' },
    { name: 'Cincinnati', state: 'OH' },
    { name: 'Indianapolis', state: 'IN' },
    { name: 'Kansas City', state: 'MO' },
    { name: 'St. Louis', state: 'MO' },
    // Southeast
    { name: 'Miami', state: 'FL' },
    { name: 'Tampa', state: 'FL' },
    { name: 'Orlando', state: 'FL' },
    { name: 'Jacksonville', state: 'FL' },
    { name: 'Atlanta', state: 'GA' },
    { name: 'Savannah', state: 'GA' },
    { name: 'Nashville', state: 'TN' },
    { name: 'Memphis', state: 'TN' },
    { name: 'New Orleans', state: 'LA' },
    { name: 'Charlotte', state: 'NC' },
    { name: 'Raleigh', state: 'NC' },
    { name: 'Charleston', state: 'SC' },
    { name: 'Richmond', state: 'VA' },
    // Northeast
    { name: 'Boston', state: 'MA' },
    { name: 'Cambridge', state: 'MA' },
    { name: 'Philadelphia', state: 'PA' },
    { name: 'Pittsburgh', state: 'PA' },
    { name: 'Baltimore', state: 'MD' },
    { name: 'Washington', state: 'DC' },
    { name: 'Providence', state: 'RI' },
    { name: 'Portland', state: 'ME' },
    { name: 'Burlington', state: 'VT' },
    { name: 'Newark', state: 'NJ' },
    { name: 'Jersey City', state: 'NJ' },
    { name: 'New Haven', state: 'CT' },
    { name: 'Hartford', state: 'CT' },
  ];

  const dateOptions = [
    { key: 'this-weekend', label: 'This Weekend', sublabel: 'Jan 31 – Feb 2' },
    { key: 'next-weekend', label: 'Next Weekend', sublabel: 'Feb 7 – 9' },
    { key: 'two-weeks', label: 'In 2 Weeks', sublabel: 'Feb 14 – 16' },
    { key: 'custom', label: 'Custom Dates', sublabel: 'Pick a range' },
  ];

  const filteredCities = cities.filter(city => 
    city.name.toLowerCase().includes(searchCity.toLowerCase()) ||
    city.state.toLowerCase().includes(searchCity.toLowerCase()) ||
    `${city.name}, ${city.state}`.toLowerCase().includes(searchCity.toLowerCase())
  );

  const filteredSubscribeCities = cities.filter(city => 
    city.name.toLowerCase().includes(subscribeCity.toLowerCase()) ||
    city.state.toLowerCase().includes(subscribeCity.toLowerCase()) ||
    `${city.name}, ${city.state}`.toLowerCase().includes(subscribeCity.toLowerCase())
  );

  // Close dropdowns when clicking outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (cityInputRef.current && !cityInputRef.current.contains(e.target)) {
        setShowCitySuggestions(false);
      }
      if (datePickerRef.current && !datePickerRef.current.contains(e.target)) {
        setShowDatePicker(false);
      }
      if (subscribeCityRef.current && !subscribeCityRef.current.contains(e.target)) {
        setShowSubscribeCitySuggestions(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const mockResults = {
    concerts: [
      { id: 1, name: "Jason Isbell and the 400 Unit", venue: "Fox Theater - Oakland", date: "Thu Jan 29", time: "8:00 PM" },
      { id: 2, name: "Cate Le Bon", venue: "The Fillmore", date: "Fri Jan 30", time: "8:00 PM" },
      { id: 3, name: "SF Symphony", venue: "Davies Symphony Hall", date: "Sat Jan 31", time: "7:30 PM" },
      { id: 4, name: "Two Friends", venue: "The Midway", date: "Sat Jan 31", time: "8:00 PM" },
      { id: 5, name: "Emo Nite", venue: "Rickshaw Stop", date: "Sat Jan 31", time: "9:00 PM" },
      { id: 6, name: "Tyler Ramsey", venue: "The Chapel", date: "Sat Jan 31", time: "9:00 PM" },
    ],
    dining: [
      { id: 1, name: "Lazy Bear", neighborhood: "Mission", rating: 4.8, price: "$$$$" },
      { id: 2, name: "Rich Table", neighborhood: "Hayes Valley", rating: 4.7, price: "$$$" },
      { id: 3, name: "Flour + Water", neighborhood: "Mission", rating: 4.5, price: "$$$" },
      { id: 4, name: "Mister Jiu's", neighborhood: "Chinatown", rating: 4.3, price: "$$$" },
      { id: 5, name: "The Morris", neighborhood: "Mission", rating: 4.7, price: "$$$" },
      { id: 6, name: "Lolinda", neighborhood: "Mission", rating: 4.6, price: "$$$" },
    ],
    events: [
      { id: 1, name: "Warriors vs. Pistons", venue: "Chase Center", date: "Fri Jan 30", time: "7:00 PM", category: "Sports" },
      { id: 2, name: "The Book of Mormon", venue: "Orpheum Theatre", date: "Thu-Sat", time: "7:00 PM", category: "Theatre" },
      { id: 3, name: "SF Sketchfest", venue: "Great American Music Hall", date: "Sat Jan 31", time: "7:00 PM", category: "Comedy" },
      { id: 4, name: "Noite de Carnaval", venue: "Grace Cathedral", date: "Fri Jan 30", time: "6:00 PM", category: "Festival" },
      { id: 5, name: "Pancakes & Booze Art Show", venue: "Crybaby", date: "Thu Jan 29", time: "7:00 PM", category: "Art" },
      { id: 6, name: "Slavic Festival 2026", venue: "2460 Sutter St", date: "Sat Jan 31", time: "11:00 AM", category: "Festival" },
    ],
    locations: [
      { id: 1, name: "Golden Gate Bridge", category: "Landmark", rating: 4.8, info: "Iconic suspension bridge" },
      { id: 2, name: "Alcatraz Island", category: "Landmark", rating: 4.7, info: "Historic prison museum" },
      { id: 3, name: "de Young Museum", category: "Museum", rating: 4.6, info: "Fine arts collection" },
      { id: 4, name: "Lands End Labyrinth", category: "Hidden Gem", rating: 4.7, info: "Stone labyrinth" },
      { id: 5, name: "Musée Mécanique", category: "Hidden Gem", rating: 4.5, info: "Vintage arcade" },
      { id: 6, name: "Seward Street Slides", category: "Activity", rating: 4.4, info: "Secret concrete slides" },
    ]
  };

  const handleSearch = () => {
    if (searchCity) {
      setIsSearching(true);
      setTimeout(() => {
        setIsSearching(false);
        setHasResults(true);
      }, 1500);
    }
  };

  const handleSubscribe = async () => {
    if (!subscribeEmail || !subscribeCity) return;

    setIsSubscribing(true);
    setSubscribeError('');

    try {
      const response = await fetch('/api/subscribe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: subscribeEmail,
          city: subscribeCity
        })
      });

      const data = await response.json();

      if (response.ok) {
        setSubscribed(true);
      } else {
        setSubscribeError(data.message || data.error || 'Something went wrong');
      }
    } catch (error) {
      setSubscribeError('Failed to subscribe. Please try again.');
    } finally {
      setIsSubscribing(false);
    }
  };

  const selectCity = (city) => {
    setSearchCity(`${city.name}, ${city.state}`);
    setShowCitySuggestions(false);
  };

  const selectSubscribeCity = (city) => {
    setSubscribeCity(`${city.name}, ${city.state}`);
    setShowSubscribeCitySuggestions(false);
  };

  const formatCustomDateDisplay = () => {
    if (customStartDate && customEndDate) {
      const start = new Date(customStartDate);
      const end = new Date(customEndDate);
      const formatDate = (d) => d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
      return `${formatDate(start)} – ${formatDate(end)}`;
    }
    return 'Select dates';
  };

  const categories = [
    { key: 'all', label: 'All', count: 163 },
    { key: 'concerts', label: 'Concerts', count: 24 },
    { key: 'dining', label: 'Dining', count: 58 },
    { key: 'events', label: 'Events', count: 22 },
    { key: 'locations', label: 'Places', count: 59 },
  ];

  const getFilteredResults = () => {
    if (activeCategory === 'all') {
      return {
        concerts: mockResults.concerts.slice(0, 2),
        dining: mockResults.dining.slice(0, 2),
        events: mockResults.events.slice(0, 2),
        locations: mockResults.locations.slice(0, 2)
      };
    }
    return { [activeCategory]: mockResults[activeCategory] };
  };

  const filtered = getFilteredResults();
  const selectedDate = dateOptions.find(d => d.key === searchDate);

  const getDateDisplayLabel = () => {
    if (searchDate === 'custom') {
      return customStartDate && customEndDate ? formatCustomDateDisplay() : 'Custom Dates';
    }
    return selectedDate?.label;
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: '#0D0D0D',
      fontFamily: "system-ui, -apple-system, sans-serif",
      color: '#FAFAFA',
      padding: '0',
    }}>
      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes slideDown {
          from { opacity: 0; transform: translateY(-8px); }
          to { opacity: 1; transform: translateY(0); }
        }
        input[type="date"] {
          color-scheme: dark;
        }
        input[type="date"]::-webkit-calendar-picker-indicator {
          filter: invert(1);
          opacity: 0.5;
          cursor: pointer;
        }
        input[type="date"]::-webkit-calendar-picker-indicator:hover {
          opacity: 0.8;
        }
      `}</style>
      
      {/* Header */}
      <header style={{
        padding: '24px 40px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        borderBottom: '1px solid rgba(255,255,255,0.08)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: '36px',
            height: '36px',
            background: 'linear-gradient(135deg, #FF6B35 0%, #F7C59F 100%)',
            borderRadius: '10px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '18px',
          }}>◈</div>
          <span style={{
            fontSize: '20px',
            fontWeight: '700',
            letterSpacing: '-0.02em',
          }}>WEEKENDER</span>
        </div>
        
        {/* Tabs */}
        <div style={{
          display: 'flex',
          background: 'rgba(255,255,255,0.05)',
          borderRadius: '12px',
          padding: '4px',
        }}>
          <button
            onClick={() => setActiveTab('search')}
            style={{
              padding: '10px 24px',
              fontSize: '13px',
              fontWeight: '600',
              letterSpacing: '0.02em',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
              transition: 'all 0.2s',
              background: activeTab === 'search' ? '#FAFAFA' : 'transparent',
              color: activeTab === 'search' ? '#0D0D0D' : 'rgba(255,255,255,0.5)',
            }}
          >
            Explore
          </button>
          <button
            onClick={() => setActiveTab('subscribe')}
            style={{
              padding: '10px 24px',
              fontSize: '13px',
              fontWeight: '600',
              letterSpacing: '0.02em',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
              transition: 'all 0.2s',
              background: activeTab === 'subscribe' ? '#FAFAFA' : 'transparent',
              color: activeTab === 'subscribe' ? '#0D0D0D' : 'rgba(255,255,255,0.5)',
            }}
          >
            Subscribe
          </button>
        </div>
        
        <div style={{ width: '120px' }} />
      </header>

      {/* Main Content */}
      <main style={{ padding: '48px 40px', maxWidth: '1400px', margin: '0 auto' }}>
        {activeTab === 'subscribe' ? (
          /* Subscribe Tab */
          <div style={{
            maxWidth: '560px',
            margin: '80px auto',
            textAlign: 'center',
          }}>
            {!subscribed ? (
              <>
                <div style={{
                  width: '80px',
                  height: '80px',
                  background: 'linear-gradient(135deg, #FF6B35 0%, #F7C59F 100%)',
                  borderRadius: '24px',
                  margin: '0 auto 32px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '36px',
                }}>✉</div>
                <h1 style={{
                  fontSize: '42px',
                  fontWeight: '700',
                  letterSpacing: '-0.03em',
                  marginBottom: '16px',
                  lineHeight: '1.1',
                }}>Your weekend,<br />curated weekly</h1>
                <p style={{
                  fontSize: '17px',
                  color: 'rgba(255,255,255,0.5)',
                  marginBottom: '48px',
                  lineHeight: '1.6',
                }}>
                  Get personalized recommendations for concerts, restaurants, events, and hidden gems delivered every Thursday.
                </p>
                
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  <input
                    type="email"
                    placeholder="your@email.com"
                    value={subscribeEmail}
                    onChange={(e) => setSubscribeEmail(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '18px 24px',
                      fontSize: '16px',
                      border: '2px solid rgba(255,255,255,0.1)',
                      borderRadius: '14px',
                      background: 'rgba(255,255,255,0.03)',
                      color: '#FAFAFA',
                      outline: 'none',
                      transition: 'border-color 0.2s',
                    }}
                    onFocus={(e) => e.target.style.borderColor = 'rgba(255,255,255,0.3)'}
                    onBlur={(e) => e.target.style.borderColor = 'rgba(255,255,255,0.1)'}
                  />
                  
                  {/* City Autocomplete for Subscribe */}
                  <div ref={subscribeCityRef} style={{ position: 'relative' }}>
                    <input
                      type="text"
                      placeholder="Search for a city..."
                      value={subscribeCity}
                      onChange={(e) => {
                        setSubscribeCity(e.target.value);
                        setShowSubscribeCitySuggestions(true);
                      }}
                      onFocus={() => setShowSubscribeCitySuggestions(true)}
                      style={{
                        width: '100%',
                        padding: '18px 24px',
                        fontSize: '16px',
                        border: '2px solid rgba(255,255,255,0.1)',
                        borderRadius: '14px',
                        background: 'rgba(255,255,255,0.03)',
                        color: '#FAFAFA',
                        outline: 'none',
                        transition: 'border-color 0.2s',
                      }}
                    />
                    {showSubscribeCitySuggestions && subscribeCity && filteredSubscribeCities.length > 0 && (
                      <div style={{
                        position: 'absolute',
                        top: '100%',
                        left: 0,
                        right: 0,
                        marginTop: '8px',
                        background: '#1A1A1A',
                        border: '1px solid rgba(255,255,255,0.1)',
                        borderRadius: '14px',
                        overflow: 'hidden',
                        zIndex: 100,
                        maxHeight: '280px',
                        overflowY: 'auto',
                        animation: 'slideDown 0.15s ease',
                      }}>
                        {filteredSubscribeCities.slice(0, 8).map((city, i) => (
                          <button
                            key={`${city.name}-${city.state}`}
                            onClick={() => selectSubscribeCity(city)}
                            style={{
                              width: '100%',
                              padding: '14px 24px',
                              display: 'flex',
                              alignItems: 'center',
                              gap: '12px',
                              background: 'transparent',
                              border: 'none',
                              borderBottom: i < Math.min(filteredSubscribeCities.length, 8) - 1 ? '1px solid rgba(255,255,255,0.06)' : 'none',
                              color: '#FAFAFA',
                              fontSize: '15px',
                              cursor: 'pointer',
                              textAlign: 'left',
                              transition: 'background 0.15s',
                            }}
                            onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.05)'}
                            onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                          >
                            <span style={{ color: 'rgba(255,255,255,0.3)', fontSize: '18px' }}>◎</span>
                            <span>{city.name}</span>
                            <span style={{ color: 'rgba(255,255,255,0.4)', marginLeft: 'auto' }}>{city.state}</span>
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                  
                  <button
                    onClick={handleSubscribe}
                    disabled={isSubscribing || !subscribeEmail || !subscribeCity}
                    style={{
                      width: '100%',
                      padding: '18px 24px',
                      fontSize: '16px',
                      fontWeight: '600',
                      border: 'none',
                      borderRadius: '14px',
                      background: (isSubscribing || !subscribeEmail || !subscribeCity)
                        ? 'rgba(255,255,255,0.1)'
                        : 'linear-gradient(135deg, #FF6B35 0%, #FF8F5F 100%)',
                      color: (isSubscribing || !subscribeEmail || !subscribeCity)
                        ? 'rgba(255,255,255,0.3)'
                        : '#FAFAFA',
                      cursor: (isSubscribing || !subscribeEmail || !subscribeCity)
                        ? 'not-allowed'
                        : 'pointer',
                      transition: 'transform 0.2s, box-shadow 0.2s',
                    }}
                    onMouseEnter={(e) => {
                      if (!isSubscribing && subscribeEmail && subscribeCity) {
                        e.target.style.transform = 'translateY(-2px)';
                        e.target.style.boxShadow = '0 8px 24px rgba(255,107,53,0.3)';
                      }
                    }}
                    onMouseLeave={(e) => {
                      e.target.style.transform = 'translateY(0)';
                      e.target.style.boxShadow = 'none';
                    }}
                  >
                    {isSubscribing ? (
                      <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '12px' }}>
                        <span style={{
                          width: '18px',
                          height: '18px',
                          border: '2px solid rgba(255,255,255,0.3)',
                          borderTopColor: '#FAFAFA',
                          borderRadius: '50%',
                          animation: 'spin 0.8s linear infinite',
                        }} />
                        Subscribing...
                      </span>
                    ) : 'Subscribe to Weekly Digest'}
                  </button>

                  {subscribeError && (
                    <p style={{
                      fontSize: '14px',
                      color: '#F87171',
                      marginTop: '12px',
                      textAlign: 'center',
                    }}>
                      {subscribeError}
                    </p>
                  )}
                </div>

                <p style={{
                  fontSize: '13px',
                  color: 'rgba(255,255,255,0.3)',
                  marginTop: '24px',
                }}>
                  Powered by multi-agent AI • Ticketmaster • Google Places • Web Search
                </p>
              </>
            ) : (
              <div style={{ animation: 'fadeIn 0.5s ease' }}>
                <div style={{
                  width: '80px',
                  height: '80px',
                  background: 'linear-gradient(135deg, #22C55E 0%, #86EFAC 100%)',
                  borderRadius: '24px',
                  margin: '0 auto 32px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '36px',
                }}>✓</div>
                <h1 style={{
                  fontSize: '42px',
                  fontWeight: '700',
                  letterSpacing: '-0.03em',
                  marginBottom: '16px',
                }}>You're in!</h1>
                <p style={{
                  fontSize: '17px',
                  color: 'rgba(255,255,255,0.5)',
                  lineHeight: '1.6',
                }}>
                  We'll send your first curated weekend guide for <strong style={{ color: '#FAFAFA' }}>{subscribeCity}</strong> this Thursday.
                </p>
              </div>
            )}
          </div>
        ) : (
          /* Search Tab */
          <>
            {!hasResults ? (
              /* Search Form */
              <div style={{
                maxWidth: '640px',
                margin: '60px auto',
                textAlign: 'center',
              }}>
                <h1 style={{
                  fontSize: '52px',
                  fontWeight: '700',
                  letterSpacing: '-0.03em',
                  marginBottom: '16px',
                  lineHeight: '1.1',
                }}>Discover your<br />perfect weekend</h1>
                <p style={{
                  fontSize: '17px',
                  color: 'rgba(255,255,255,0.5)',
                  marginBottom: '48px',
                }}>
                  AI-powered search across concerts, dining, events & attractions
                </p>
                
                <div style={{
                  display: 'flex',
                  gap: '12px',
                  marginBottom: '16px',
                }}>
                  {/* City Autocomplete */}
                  <div ref={cityInputRef} style={{ flex: 1, position: 'relative' }}>
                    <input
                      type="text"
                      placeholder="Search for a city..."
                      value={searchCity}
                      onChange={(e) => {
                        setSearchCity(e.target.value);
                        setShowCitySuggestions(true);
                      }}
                      onFocus={() => setShowCitySuggestions(true)}
                      style={{
                        width: '100%',
                        padding: '20px 24px',
                        fontSize: '17px',
                        border: '2px solid rgba(255,255,255,0.1)',
                        borderRadius: '16px',
                        background: 'rgba(255,255,255,0.03)',
                        color: '#FAFAFA',
                        outline: 'none',
                      }}
                    />
                    {showCitySuggestions && filteredCities.length > 0 && (
                      <div style={{
                        position: 'absolute',
                        top: '100%',
                        left: 0,
                        right: 0,
                        marginTop: '8px',
                        background: '#1A1A1A',
                        border: '1px solid rgba(255,255,255,0.1)',
                        borderRadius: '16px',
                        overflow: 'hidden',
                        zIndex: 100,
                        maxHeight: '320px',
                        overflowY: 'auto',
                        animation: 'slideDown 0.15s ease',
                      }}>
                        {filteredCities.slice(0, 8).map((city, i) => (
                          <button
                            key={`${city.name}-${city.state}`}
                            onClick={() => selectCity(city)}
                            style={{
                              width: '100%',
                              padding: '16px 24px',
                              display: 'flex',
                              alignItems: 'center',
                              gap: '12px',
                              background: 'transparent',
                              border: 'none',
                              borderBottom: i < Math.min(filteredCities.length, 8) - 1 ? '1px solid rgba(255,255,255,0.06)' : 'none',
                              color: '#FAFAFA',
                              fontSize: '16px',
                              cursor: 'pointer',
                              textAlign: 'left',
                              transition: 'background 0.15s',
                            }}
                            onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.05)'}
                            onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                          >
                            <span style={{ color: 'rgba(255,255,255,0.3)', fontSize: '20px' }}>◎</span>
                            <span>{city.name}</span>
                            <span style={{ color: 'rgba(255,255,255,0.4)', marginLeft: 'auto' }}>{city.state}</span>
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                  
                  {/* Custom Date Picker */}
                  <div ref={datePickerRef} style={{ position: 'relative' }}>
                    <button
                      onClick={() => setShowDatePicker(!showDatePicker)}
                      style={{
                        padding: '20px 24px',
                        fontSize: '17px',
                        border: '2px solid rgba(255,255,255,0.1)',
                        borderRadius: '16px',
                        background: 'rgba(255,255,255,0.03)',
                        color: '#FAFAFA',
                        cursor: 'pointer',
                        minWidth: '200px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        gap: '12px',
                        transition: 'border-color 0.2s',
                      }}
                    >
                      <span>{getDateDisplayLabel()}</span>
                      <span style={{ 
                        color: 'rgba(255,255,255,0.4)',
                        transform: showDatePicker ? 'rotate(180deg)' : 'rotate(0)',
                        transition: 'transform 0.2s',
                      }}>▾</span>
                    </button>
                    
                    {showDatePicker && (
                      <div style={{
                        position: 'absolute',
                        top: '100%',
                        right: 0,
                        marginTop: '8px',
                        background: '#1A1A1A',
                        border: '1px solid rgba(255,255,255,0.1)',
                        borderRadius: '16px',
                        overflow: 'hidden',
                        zIndex: 100,
                        minWidth: '280px',
                        animation: 'slideDown 0.15s ease',
                      }}>
                        {dateOptions.map((option, i) => (
                          <button
                            key={option.key}
                            onClick={() => {
                              setSearchDate(option.key);
                              if (option.key !== 'custom') {
                                setShowDatePicker(false);
                              }
                            }}
                            style={{
                              width: '100%',
                              padding: '16px 24px',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'space-between',
                              background: searchDate === option.key ? 'rgba(255,107,53,0.1)' : 'transparent',
                              border: 'none',
                              borderBottom: option.key !== 'custom' ? '1px solid rgba(255,255,255,0.06)' : 'none',
                              color: '#FAFAFA',
                              fontSize: '15px',
                              cursor: 'pointer',
                              textAlign: 'left',
                              transition: 'background 0.15s',
                            }}
                            onMouseEnter={(e) => {
                              if (searchDate !== option.key) e.currentTarget.style.background = 'rgba(255,255,255,0.05)';
                            }}
                            onMouseLeave={(e) => {
                              if (searchDate !== option.key) e.currentTarget.style.background = 'transparent';
                            }}
                          >
                            <span style={{ fontWeight: searchDate === option.key ? '600' : '400' }}>{option.label}</span>
                            <span style={{ color: 'rgba(255,255,255,0.4)', fontSize: '13px' }}>{option.sublabel}</span>
                          </button>
                        ))}
                        
                        {/* Custom Date Inputs */}
                        {searchDate === 'custom' && (
                          <div style={{
                            padding: '20px 24px',
                            borderTop: '1px solid rgba(255,255,255,0.06)',
                            display: 'flex',
                            flexDirection: 'column',
                            gap: '12px',
                          }}>
                            <div>
                              <label style={{
                                display: 'block',
                                fontSize: '12px',
                                color: 'rgba(255,255,255,0.4)',
                                marginBottom: '8px',
                                textTransform: 'uppercase',
                                letterSpacing: '0.05em',
                              }}>Start Date</label>
                              <input
                                type="date"
                                value={customStartDate}
                                onChange={(e) => setCustomStartDate(e.target.value)}
                                style={{
                                  width: '100%',
                                  padding: '12px 16px',
                                  fontSize: '15px',
                                  border: '1px solid rgba(255,255,255,0.15)',
                                  borderRadius: '10px',
                                  background: 'rgba(255,255,255,0.05)',
                                  color: '#FAFAFA',
                                  outline: 'none',
                                }}
                              />
                            </div>
                            <div>
                              <label style={{
                                display: 'block',
                                fontSize: '12px',
                                color: 'rgba(255,255,255,0.4)',
                                marginBottom: '8px',
                                textTransform: 'uppercase',
                                letterSpacing: '0.05em',
                              }}>End Date</label>
                              <input
                                type="date"
                                value={customEndDate}
                                onChange={(e) => setCustomEndDate(e.target.value)}
                                min={customStartDate}
                                style={{
                                  width: '100%',
                                  padding: '12px 16px',
                                  fontSize: '15px',
                                  border: '1px solid rgba(255,255,255,0.15)',
                                  borderRadius: '10px',
                                  background: 'rgba(255,255,255,0.05)',
                                  color: '#FAFAFA',
                                  outline: 'none',
                                }}
                              />
                            </div>
                            <button
                              onClick={() => setShowDatePicker(false)}
                              disabled={!customStartDate || !customEndDate}
                              style={{
                                width: '100%',
                                padding: '12px 16px',
                                fontSize: '14px',
                                fontWeight: '600',
                                border: 'none',
                                borderRadius: '10px',
                                background: customStartDate && customEndDate ? '#FF6B35' : 'rgba(255,255,255,0.1)',
                                color: customStartDate && customEndDate ? '#FAFAFA' : 'rgba(255,255,255,0.3)',
                                cursor: customStartDate && customEndDate ? 'pointer' : 'not-allowed',
                                marginTop: '4px',
                              }}
                            >
                              Apply Dates
                            </button>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
                
                <button
                  onClick={handleSearch}
                  disabled={!searchCity || isSearching}
                  style={{
                    width: '100%',
                    padding: '20px 24px',
                    fontSize: '17px',
                    fontWeight: '600',
                    border: 'none',
                    borderRadius: '16px',
                    background: searchCity ? 'linear-gradient(135deg, #FF6B35 0%, #FF8F5F 100%)' : 'rgba(255,255,255,0.1)',
                    color: searchCity ? '#FAFAFA' : 'rgba(255,255,255,0.3)',
                    cursor: searchCity ? 'pointer' : 'not-allowed',
                    transition: 'all 0.2s',
                  }}
                >
                  {isSearching ? (
                    <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '12px' }}>
                      <span style={{
                        width: '20px',
                        height: '20px',
                        border: '2px solid rgba(255,255,255,0.3)',
                        borderTopColor: '#FAFAFA',
                        borderRadius: '50%',
                        animation: 'spin 0.8s linear infinite',
                      }} />
                      Running 4 agents in parallel...
                    </span>
                  ) : 'Search Weekend'}
                </button>
                
                {/* Tip for city API integration */}
                <p style={{
                  fontSize: '12px',
                  color: 'rgba(255,255,255,0.25)',
                  marginTop: '24px',
                }}>
                  💡 Connect to Google Places API for comprehensive city autocomplete
                </p>
              </div>
            ) : (
              /* Results View */
              <>
                {/* Results Header */}
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'flex-start',
                  marginBottom: '32px',
                }}>
                  <div>
                    <h1 style={{
                      fontSize: '36px',
                      fontWeight: '700',
                      letterSpacing: '-0.02em',
                      marginBottom: '8px',
                    }}>{searchCity.split(',')[0]}</h1>
                    <p style={{ color: 'rgba(255,255,255,0.5)' }}>
                      {searchDate === 'custom' ? formatCustomDateDisplay() : selectedDate?.sublabel}, 2026 • 163 results
                    </p>
                  </div>
                  <button
                    onClick={() => { setHasResults(false); setSearchCity(''); }}
                    style={{
                      padding: '12px 20px',
                      fontSize: '14px',
                      fontWeight: '500',
                      border: '1px solid rgba(255,255,255,0.15)',
                      borderRadius: '10px',
                      background: 'transparent',
                      color: '#FAFAFA',
                      cursor: 'pointer',
                    }}
                  >
                    New Search
                  </button>
                </div>
                
                {/* Category Filters */}
                <div style={{
                  display: 'flex',
                  gap: '10px',
                  marginBottom: '40px',
                  flexWrap: 'wrap',
                }}>
                  {categories.map(cat => (
                    <button
                      key={cat.key}
                      onClick={() => setActiveCategory(cat.key)}
                      style={{
                        padding: '12px 20px',
                        fontSize: '13px',
                        fontWeight: '500',
                        border: activeCategory === cat.key ? 'none' : '1px solid rgba(255,255,255,0.12)',
                        borderRadius: '100px',
                        background: activeCategory === cat.key ? '#FAFAFA' : 'transparent',
                        color: activeCategory === cat.key ? '#0D0D0D' : 'rgba(255,255,255,0.6)',
                        cursor: 'pointer',
                        transition: 'all 0.2s',
                      }}
                    >
                      {cat.label} <span style={{ opacity: 0.5 }}>{cat.count}</span>
                    </button>
                  ))}
                </div>
                
                {/* Results Grid */}
                <div>
                  {/* Concerts */}
                  {filtered.concerts && (
                    <section style={{ marginBottom: '48px' }}>
                      <div style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        marginBottom: '20px',
                      }}>
                        <h2 style={{
                          fontSize: '14px',
                          fontWeight: '600',
                          letterSpacing: '0.08em',
                          textTransform: 'uppercase',
                          color: 'rgba(255,255,255,0.4)',
                        }}>♪ Concerts</h2>
                        {activeCategory === 'all' && (
                          <button style={{
                            fontSize: '13px',
                            color: '#FF6B35',
                            background: 'none',
                            border: 'none',
                            cursor: 'pointer',
                          }}>View all 24 →</button>
                        )}
                      </div>
                      <div style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
                        gap: '16px',
                      }}>
                        {filtered.concerts.map(item => (
                          <div key={item.id} style={{
                            background: 'rgba(255,255,255,0.03)',
                            border: '1px solid rgba(255,255,255,0.06)',
                            borderRadius: '16px',
                            padding: '24px',
                            cursor: 'pointer',
                            transition: 'all 0.2s',
                          }}
                          onMouseEnter={(e) => {
                            e.currentTarget.style.background = 'rgba(255,255,255,0.06)';
                            e.currentTarget.style.transform = 'translateY(-2px)';
                          }}
                          onMouseLeave={(e) => {
                            e.currentTarget.style.background = 'rgba(255,255,255,0.03)';
                            e.currentTarget.style.transform = 'translateY(0)';
                          }}
                          >
                            <p style={{
                              fontSize: '12px',
                              color: '#FF6B35',
                              fontWeight: '600',
                              marginBottom: '8px',
                            }}>{item.date} • {item.time}</p>
                            <h3 style={{
                              fontSize: '18px',
                              fontWeight: '600',
                              marginBottom: '8px',
                              lineHeight: '1.3',
                            }}>{item.name}</h3>
                            <p style={{
                              fontSize: '14px',
                              color: 'rgba(255,255,255,0.5)',
                            }}>{item.venue}</p>
                          </div>
                        ))}
                      </div>
                    </section>
                  )}
                  
                  {/* Dining */}
                  {filtered.dining && (
                    <section style={{ marginBottom: '48px' }}>
                      <div style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        marginBottom: '20px',
                      }}>
                        <h2 style={{
                          fontSize: '14px',
                          fontWeight: '600',
                          letterSpacing: '0.08em',
                          textTransform: 'uppercase',
                          color: 'rgba(255,255,255,0.4)',
                        }}>◎ Dining</h2>
                        {activeCategory === 'all' && (
                          <button style={{
                            fontSize: '13px',
                            color: '#FF6B35',
                            background: 'none',
                            border: 'none',
                            cursor: 'pointer',
                          }}>View all 58 →</button>
                        )}
                      </div>
                      <div style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
                        gap: '16px',
                      }}>
                        {filtered.dining.map(item => (
                          <div key={item.id} style={{
                            background: 'rgba(255,255,255,0.03)',
                            border: '1px solid rgba(255,255,255,0.06)',
                            borderRadius: '16px',
                            padding: '24px',
                            cursor: 'pointer',
                            transition: 'all 0.2s',
                          }}
                          onMouseEnter={(e) => {
                            e.currentTarget.style.background = 'rgba(255,255,255,0.06)';
                            e.currentTarget.style.transform = 'translateY(-2px)';
                          }}
                          onMouseLeave={(e) => {
                            e.currentTarget.style.background = 'rgba(255,255,255,0.03)';
                            e.currentTarget.style.transform = 'translateY(0)';
                          }}
                          >
                            <div style={{
                              display: 'flex',
                              justifyContent: 'space-between',
                              alignItems: 'flex-start',
                              marginBottom: '8px',
                            }}>
                              <p style={{
                                fontSize: '12px',
                                color: '#22C55E',
                                fontWeight: '600',
                              }}>{item.neighborhood}</p>
                              <span style={{
                                fontSize: '12px',
                                color: 'rgba(255,255,255,0.4)',
                              }}>{item.price}</span>
                            </div>
                            <h3 style={{
                              fontSize: '18px',
                              fontWeight: '600',
                              marginBottom: '8px',
                            }}>{item.name}</h3>
                            <p style={{
                              fontSize: '14px',
                              color: 'rgba(255,255,255,0.5)',
                            }}>★ {item.rating}</p>
                          </div>
                        ))}
                      </div>
                    </section>
                  )}
                  
                  {/* Events */}
                  {filtered.events && (
                    <section style={{ marginBottom: '48px' }}>
                      <div style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        marginBottom: '20px',
                      }}>
                        <h2 style={{
                          fontSize: '14px',
                          fontWeight: '600',
                          letterSpacing: '0.08em',
                          textTransform: 'uppercase',
                          color: 'rgba(255,255,255,0.4)',
                        }}>◈ Events</h2>
                        {activeCategory === 'all' && (
                          <button style={{
                            fontSize: '13px',
                            color: '#FF6B35',
                            background: 'none',
                            border: 'none',
                            cursor: 'pointer',
                          }}>View all 22 →</button>
                        )}
                      </div>
                      <div style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
                        gap: '16px',
                      }}>
                        {filtered.events.map(item => (
                          <div key={item.id} style={{
                            background: 'rgba(255,255,255,0.03)',
                            border: '1px solid rgba(255,255,255,0.06)',
                            borderRadius: '16px',
                            padding: '24px',
                            cursor: 'pointer',
                            transition: 'all 0.2s',
                          }}
                          onMouseEnter={(e) => {
                            e.currentTarget.style.background = 'rgba(255,255,255,0.06)';
                            e.currentTarget.style.transform = 'translateY(-2px)';
                          }}
                          onMouseLeave={(e) => {
                            e.currentTarget.style.background = 'rgba(255,255,255,0.03)';
                            e.currentTarget.style.transform = 'translateY(0)';
                          }}
                          >
                            <div style={{
                              display: 'flex',
                              justifyContent: 'space-between',
                              alignItems: 'flex-start',
                              marginBottom: '8px',
                            }}>
                              <p style={{
                                fontSize: '12px',
                                color: '#A78BFA',
                                fontWeight: '600',
                              }}>{item.date} • {item.time}</p>
                              <span style={{
                                fontSize: '11px',
                                padding: '4px 10px',
                                background: 'rgba(167,139,250,0.15)',
                                color: '#A78BFA',
                                borderRadius: '100px',
                              }}>{item.category}</span>
                            </div>
                            <h3 style={{
                              fontSize: '18px',
                              fontWeight: '600',
                              marginBottom: '8px',
                            }}>{item.name}</h3>
                            <p style={{
                              fontSize: '14px',
                              color: 'rgba(255,255,255,0.5)',
                            }}>{item.venue}</p>
                          </div>
                        ))}
                      </div>
                    </section>
                  )}
                  
                  {/* Locations */}
                  {filtered.locations && (
                    <section>
                      <div style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        marginBottom: '20px',
                      }}>
                        <h2 style={{
                          fontSize: '14px',
                          fontWeight: '600',
                          letterSpacing: '0.08em',
                          textTransform: 'uppercase',
                          color: 'rgba(255,255,255,0.4)',
                        }}>◇ Places</h2>
                        {activeCategory === 'all' && (
                          <button style={{
                            fontSize: '13px',
                            color: '#FF6B35',
                            background: 'none',
                            border: 'none',
                            cursor: 'pointer',
                          }}>View all 59 →</button>
                        )}
                      </div>
                      <div style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
                        gap: '16px',
                      }}>
                        {filtered.locations.map(item => (
                          <div key={item.id} style={{
                            background: 'rgba(255,255,255,0.03)',
                            border: '1px solid rgba(255,255,255,0.06)',
                            borderRadius: '16px',
                            padding: '24px',
                            cursor: 'pointer',
                            transition: 'all 0.2s',
                          }}
                          onMouseEnter={(e) => {
                            e.currentTarget.style.background = 'rgba(255,255,255,0.06)';
                            e.currentTarget.style.transform = 'translateY(-2px)';
                          }}
                          onMouseLeave={(e) => {
                            e.currentTarget.style.background = 'rgba(255,255,255,0.03)';
                            e.currentTarget.style.transform = 'translateY(0)';
                          }}
                          >
                            <div style={{
                              display: 'flex',
                              justifyContent: 'space-between',
                              alignItems: 'flex-start',
                              marginBottom: '8px',
                            }}>
                              <span style={{
                                fontSize: '11px',
                                padding: '4px 10px',
                                background: 'rgba(56,189,248,0.15)',
                                color: '#38BDF8',
                                borderRadius: '100px',
                              }}>{item.category}</span>
                              <span style={{
                                fontSize: '12px',
                                color: 'rgba(255,255,255,0.4)',
                              }}>★ {item.rating}</span>
                            </div>
                            <h3 style={{
                              fontSize: '18px',
                              fontWeight: '600',
                              marginBottom: '8px',
                            }}>{item.name}</h3>
                            <p style={{
                              fontSize: '14px',
                              color: 'rgba(255,255,255,0.5)',
                            }}>{item.info}</p>
                          </div>
                        ))}
                      </div>
                    </section>
                  )}
                </div>
              </>
            )}
          </>
        )}
      </main>
    </div>
  );
};

export default WeekenderApp;
