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
  const [searchError, setSearchError] = useState('');
  const [results, setResults] = useState(null);
  const [subscribed, setSubscribed] = useState(false);
  const [isSubscribing, setIsSubscribing] = useState(false);
  const [subscribeError, setSubscribeError] = useState('');
  const [showCitySuggestions, setShowCitySuggestions] = useState(false);
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [showSubscribeCitySuggestions, setShowSubscribeCitySuggestions] = useState(false);
  const [weatherData, setWeatherData] = useState(null);
  const [selectedCityData, setSelectedCityData] = useState(null);

  // Category-specific filters (arrays for multiselect, empty = all)
  const [concertFilters, setConcertFilters] = useState({ genres: [], days: [], times: [] });
  const [diningFilters, setDiningFilters] = useState({ cuisines: [], prices: [], ratings: [] });
  const [eventFilters, setEventFilters] = useState({ categories: [], days: [] });
  const [placeFilters, setPlaceFilters] = useState({ categories: [], ratings: [] });

  const cityInputRef = useRef(null);
  const datePickerRef = useRef(null);
  const subscribeCityRef = useRef(null);

  // Expanded city list with coordinates for weather API
  const cities = [
    // California
    { name: 'San Francisco', state: 'CA', lat: 37.7749, lon: -122.4194 },
    { name: 'Los Angeles', state: 'CA', lat: 34.0522, lon: -118.2437 },
    { name: 'San Diego', state: 'CA', lat: 32.7157, lon: -117.1611 },
    { name: 'San Jose', state: 'CA', lat: 37.3382, lon: -121.8863 },
    { name: 'Oakland', state: 'CA', lat: 37.8044, lon: -122.2712 },
    { name: 'Sacramento', state: 'CA', lat: 38.5816, lon: -121.4944 },
    { name: 'Santa Monica', state: 'CA', lat: 34.0195, lon: -118.4912 },
    { name: 'Berkeley', state: 'CA', lat: 37.8716, lon: -122.2727 },
    { name: 'Pasadena', state: 'CA', lat: 34.1478, lon: -118.1445 },
    { name: 'Long Beach', state: 'CA', lat: 33.7701, lon: -118.1937 },
    // New York
    { name: 'New York', state: 'NY', lat: 40.7128, lon: -74.0060 },
    { name: 'Brooklyn', state: 'NY', lat: 40.6782, lon: -73.9442 },
    { name: 'Queens', state: 'NY', lat: 40.7282, lon: -73.7949 },
    { name: 'Buffalo', state: 'NY', lat: 42.8864, lon: -78.8784 },
    { name: 'Rochester', state: 'NY', lat: 43.1566, lon: -77.6088 },
    // Texas
    { name: 'Austin', state: 'TX', lat: 30.2672, lon: -97.7431 },
    { name: 'Houston', state: 'TX', lat: 29.7604, lon: -95.3698 },
    { name: 'Dallas', state: 'TX', lat: 32.7767, lon: -96.7970 },
    { name: 'San Antonio', state: 'TX', lat: 29.4241, lon: -98.4936 },
    { name: 'Fort Worth', state: 'TX', lat: 32.7555, lon: -97.3308 },
    { name: 'El Paso', state: 'TX', lat: 31.7619, lon: -106.4850 },
    // Pacific Northwest
    { name: 'Seattle', state: 'WA', lat: 47.6062, lon: -122.3321 },
    { name: 'Portland', state: 'OR', lat: 45.5152, lon: -122.6784 },
    { name: 'Tacoma', state: 'WA', lat: 47.2529, lon: -122.4443 },
    { name: 'Spokane', state: 'WA', lat: 47.6588, lon: -117.4260 },
    { name: 'Eugene', state: 'OR', lat: 44.0521, lon: -123.0868 },
    // Mountain
    { name: 'Denver', state: 'CO', lat: 39.7392, lon: -104.9903 },
    { name: 'Boulder', state: 'CO', lat: 40.0150, lon: -105.2705 },
    { name: 'Salt Lake City', state: 'UT', lat: 40.7608, lon: -111.8910 },
    { name: 'Phoenix', state: 'AZ', lat: 33.4484, lon: -112.0740 },
    { name: 'Tucson', state: 'AZ', lat: 32.2226, lon: -110.9747 },
    { name: 'Albuquerque', state: 'NM', lat: 35.0844, lon: -106.6504 },
    { name: 'Santa Fe', state: 'NM', lat: 35.6870, lon: -105.9378 },
    { name: 'Las Vegas', state: 'NV', lat: 36.1699, lon: -115.1398 },
    { name: 'Reno', state: 'NV', lat: 39.5296, lon: -119.8138 },
    // Midwest
    { name: 'Chicago', state: 'IL', lat: 41.8781, lon: -87.6298 },
    { name: 'Minneapolis', state: 'MN', lat: 44.9778, lon: -93.2650 },
    { name: 'St. Paul', state: 'MN', lat: 44.9537, lon: -93.0900 },
    { name: 'Detroit', state: 'MI', lat: 42.3314, lon: -83.0458 },
    { name: 'Ann Arbor', state: 'MI', lat: 42.2808, lon: -83.7430 },
    { name: 'Milwaukee', state: 'WI', lat: 43.0389, lon: -87.9065 },
    { name: 'Madison', state: 'WI', lat: 43.0731, lon: -89.4012 },
    { name: 'Cleveland', state: 'OH', lat: 41.4993, lon: -81.6944 },
    { name: 'Columbus', state: 'OH', lat: 39.9612, lon: -82.9988 },
    { name: 'Cincinnati', state: 'OH', lat: 39.1031, lon: -84.5120 },
    { name: 'Indianapolis', state: 'IN', lat: 39.7684, lon: -86.1581 },
    { name: 'Kansas City', state: 'MO', lat: 39.0997, lon: -94.5786 },
    { name: 'St. Louis', state: 'MO', lat: 38.6270, lon: -90.1994 },
    // Southeast
    { name: 'Miami', state: 'FL', lat: 25.7617, lon: -80.1918 },
    { name: 'Tampa', state: 'FL', lat: 27.9506, lon: -82.4572 },
    { name: 'Orlando', state: 'FL', lat: 28.5383, lon: -81.3792 },
    { name: 'Jacksonville', state: 'FL', lat: 30.3322, lon: -81.6557 },
    { name: 'Atlanta', state: 'GA', lat: 33.7490, lon: -84.3880 },
    { name: 'Savannah', state: 'GA', lat: 32.0809, lon: -81.0912 },
    { name: 'Nashville', state: 'TN', lat: 36.1627, lon: -86.7816 },
    { name: 'Memphis', state: 'TN', lat: 35.1495, lon: -90.0490 },
    { name: 'New Orleans', state: 'LA', lat: 29.9511, lon: -90.0715 },
    { name: 'Charlotte', state: 'NC', lat: 35.2271, lon: -80.8431 },
    { name: 'Raleigh', state: 'NC', lat: 35.7796, lon: -78.6382 },
    { name: 'Charleston', state: 'SC', lat: 32.7765, lon: -79.9311 },
    { name: 'Richmond', state: 'VA', lat: 37.5407, lon: -77.4360 },
    // Northeast
    { name: 'Boston', state: 'MA', lat: 42.3601, lon: -71.0589 },
    { name: 'Cambridge', state: 'MA', lat: 42.3736, lon: -71.1097 },
    { name: 'Philadelphia', state: 'PA', lat: 39.9526, lon: -75.1652 },
    { name: 'Pittsburgh', state: 'PA', lat: 40.4406, lon: -79.9959 },
    { name: 'Baltimore', state: 'MD', lat: 39.2904, lon: -76.6122 },
    { name: 'Washington', state: 'DC', lat: 38.9072, lon: -77.0369 },
    { name: 'Providence', state: 'RI', lat: 41.8240, lon: -71.4128 },
    { name: 'Portland', state: 'ME', lat: 43.6591, lon: -70.2568 },
    { name: 'Burlington', state: 'VT', lat: 44.4759, lon: -73.2121 },
    { name: 'Newark', state: 'NJ', lat: 40.7357, lon: -74.1724 },
    { name: 'Jersey City', state: 'NJ', lat: 40.7178, lon: -74.0431 },
    { name: 'New Haven', state: 'CT', lat: 41.3083, lon: -72.9279 },
    { name: 'Hartford', state: 'CT', lat: 41.7658, lon: -72.6734 },
  ];

  // Calculate dynamic weekend dates
  const getWeekendDates = (weeksAhead = 0) => {
    const today = new Date();
    const dayOfWeek = today.getDay(); // 0 = Sunday, 6 = Saturday

    // Find days until this Friday (day 5)
    let daysUntilFriday = (5 - dayOfWeek + 7) % 7;
    if (daysUntilFriday === 0 && today.getHours() >= 12) {
      // If it's Friday afternoon or later, move to next weekend
      daysUntilFriday = 7;
    }

    // Add weeks ahead
    daysUntilFriday += weeksAhead * 7;

    const friday = new Date(today);
    friday.setDate(today.getDate() + daysUntilFriday);

    const sunday = new Date(friday);
    sunday.setDate(friday.getDate() + 2);

    const formatShort = (d) => d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    return `${formatShort(friday)} – ${formatShort(sunday)}`;
  };

  const dateOptions = [
    { key: 'this-weekend', label: 'This Weekend', sublabel: getWeekendDates(0) },
    { key: 'next-weekend', label: 'Next Weekend', sublabel: getWeekendDates(1) },
    { key: 'two-weeks', label: 'In 2 Weeks', sublabel: getWeekendDates(2) },
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

  // WMO Weather code to icon/description mapping
  const weatherCodeMap = {
    0: { icon: '☀️', desc: 'Clear', color: '#FFD700' },
    1: { icon: '🌤️', desc: 'Mostly Clear', color: '#FFD700' },
    2: { icon: '⛅', desc: 'Partly Cloudy', color: '#87CEEB' },
    3: { icon: '☁️', desc: 'Overcast', color: '#A9A9A9' },
    45: { icon: '🌫️', desc: 'Foggy', color: '#C0C0C0' },
    48: { icon: '🌫️', desc: 'Icy Fog', color: '#B0C4DE' },
    51: { icon: '🌧️', desc: 'Light Drizzle', color: '#4682B4' },
    53: { icon: '🌧️', desc: 'Drizzle', color: '#4682B4' },
    55: { icon: '🌧️', desc: 'Heavy Drizzle', color: '#4169E1' },
    61: { icon: '🌧️', desc: 'Light Rain', color: '#4682B4' },
    63: { icon: '🌧️', desc: 'Rain', color: '#4169E1' },
    65: { icon: '🌧️', desc: 'Heavy Rain', color: '#1E3A8A' },
    66: { icon: '🌨️', desc: 'Freezing Rain', color: '#87CEEB' },
    67: { icon: '🌨️', desc: 'Heavy Freezing Rain', color: '#6495ED' },
    71: { icon: '❄️', desc: 'Light Snow', color: '#E0FFFF' },
    73: { icon: '❄️', desc: 'Snow', color: '#ADD8E6' },
    75: { icon: '❄️', desc: 'Heavy Snow', color: '#B0E0E6' },
    77: { icon: '🌨️', desc: 'Snow Grains', color: '#F0F8FF' },
    80: { icon: '🌦️', desc: 'Light Showers', color: '#6495ED' },
    81: { icon: '🌦️', desc: 'Showers', color: '#4682B4' },
    82: { icon: '⛈️', desc: 'Heavy Showers', color: '#4169E1' },
    85: { icon: '🌨️', desc: 'Snow Showers', color: '#B0E0E6' },
    86: { icon: '🌨️', desc: 'Heavy Snow Showers', color: '#87CEEB' },
    95: { icon: '⛈️', desc: 'Thunderstorm', color: '#483D8B' },
    96: { icon: '⛈️', desc: 'Thunderstorm + Hail', color: '#4B0082' },
    99: { icon: '⛈️', desc: 'Heavy Thunderstorm', color: '#2F0854' },
  };

  const getWeatherInfo = (code) => {
    return weatherCodeMap[code] || { icon: '🌡️', desc: 'Unknown', color: '#888' };
  };

  // Fetch weather when city and date are selected
  // Fetch weather using actual dates from results
  const fetchWeather = async (cityData, startDate, endDate) => {
    if (!cityData || !cityData.lat || !cityData.lon || !startDate || !endDate) return;

    // Check if dates are too far out (Open-Meteo supports 16 days)
    const today = new Date();
    const start = new Date(startDate);
    const daysOut = Math.ceil((start - today) / (1000 * 60 * 60 * 24));

    if (daysOut > 14) {
      setWeatherData('unavailable');
      return;
    }

    try {
      const url = `https://api.open-meteo.com/v1/forecast?latitude=${cityData.lat}&longitude=${cityData.lon}&daily=weather_code,temperature_2m_max,temperature_2m_min,wind_speed_10m_max&temperature_unit=fahrenheit&timezone=auto&start_date=${startDate}&end_date=${endDate}`;

      const response = await fetch(url);
      const data = await response.json();

      if (data.daily && data.daily.time) {
        const days = data.daily.time.map((date, i) => ({
          date,
          dayName: new Date(date + 'T12:00:00').toLocaleDateString('en-US', { weekday: 'short' }),
          weatherCode: data.daily.weather_code[i],
          high: Math.round(data.daily.temperature_2m_max[i]),
          low: Math.round(data.daily.temperature_2m_min[i]),
          wind: Math.round(data.daily.wind_speed_10m_max[i]),
        }));
        setWeatherData(days);
      } else {
        setWeatherData('unavailable');
      }
    } catch (error) {
      console.log('Weather fetch error:', error);
      setWeatherData('unavailable');
    }
  };

  // Fetch weather when results arrive (using actual dates from backend)
  useEffect(() => {
    if (hasResults && selectedCityData && results?.start_date && results?.end_date) {
      fetchWeather(selectedCityData, results.start_date, results.end_date);
    }
  }, [hasResults, selectedCityData, results?.start_date, results?.end_date]);

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

  const handleSearch = async () => {
    if (!searchCity) return;

    setIsSearching(true);
    setSearchError('');

    // Map date option to weekend param
    const weekendMap = {
      'this-weekend': 'this',
      'next-weekend': 'next',
      'two-weeks': 'two-weeks'
    };
    const weekendParam = weekendMap[searchDate] || 'this';

    try {
      const response = await fetch('https://weekenders-app.onrender.com/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          city: searchCity.split(',')[0].trim(),  // Just city name, no state
          weekend: weekendParam
        })
      });

      const data = await response.json();

      if (response.ok) {
        setResults(data);
        setHasResults(true);
      } else {
        setSearchError(data.detail || 'Search failed. Please try again.');
      }
    } catch (error) {
      setSearchError('Failed to connect. Please try again.');
    } finally {
      setIsSearching(false);
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
    setSelectedCityData(city);
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

  // Dynamic categories based on results
  const getCategories = () => {
    if (!results) return [
      { key: 'all', label: 'All', count: 0 },
      { key: 'concerts', label: 'Concerts', count: 0 },
      { key: 'dining', label: 'Dining', count: 0 },
      { key: 'events', label: 'Events', count: 0 },
      { key: 'locations', label: 'Places', count: 0 },
    ];

    const counts = {
      concerts: results.concerts?.length || 0,
      dining: results.dining?.length || 0,
      events: results.events?.length || 0,
      locations: results.locations?.length || 0,
    };
    const total = counts.concerts + counts.dining + counts.events + counts.locations;

    return [
      { key: 'all', label: 'All', count: total },
      { key: 'concerts', label: 'Concerts', count: counts.concerts },
      { key: 'dining', label: 'Dining', count: counts.dining },
      { key: 'events', label: 'Events', count: counts.events },
      { key: 'locations', label: 'Places', count: counts.locations },
    ];
  };

  const categories = getCategories();

  // Extract unique filter options from results
  const getFilterOptions = () => {
    if (!results) return {};

    // Concert genres
    const genres = new Set();
    (results.concerts || []).forEach(c => {
      if (c.genre) genres.add(c.genre);
    });

    // Concert days
    const concertDays = new Set();
    (results.concerts || []).forEach(c => {
      if (c.date) {
        const day = new Date(c.date + 'T12:00:00').toLocaleDateString('en-US', { weekday: 'short' });
        concertDays.add(day);
      }
    });

    // Dining cuisines and types
    const cuisines = new Set();
    const diningTypes = new Set(['Restaurant']);
    (results.dining || []).forEach(d => {
      if (d.cuisine) cuisines.add(d.cuisine);
      // Check if it's a bar based on name/cuisine
      const name = (d.name || '').toLowerCase();
      const cuisine = (d.cuisine || '').toLowerCase();
      if (name.includes('bar') || cuisine.includes('bar') || cuisine.includes('cocktail') || cuisine.includes('wine')) {
        diningTypes.add('Bar');
      }
    });

    // Event categories
    const eventCategories = new Set();
    (results.events || []).forEach(e => {
      if (e.category) eventCategories.add(e.category);
    });

    // Event days
    const eventDays = new Set();
    (results.events || []).forEach(e => {
      if (e.date) {
        const day = new Date(e.date + 'T12:00:00').toLocaleDateString('en-US', { weekday: 'short' });
        eventDays.add(day);
      }
    });

    // Place categories
    const placeCategories = new Set();
    (results.locations || []).forEach(l => {
      if (l.category) placeCategories.add(l.category);
    });

    return {
      genres: Array.from(genres).sort(),
      concertDays: Array.from(concertDays),
      cuisines: Array.from(cuisines).sort(),
      diningTypes: Array.from(diningTypes),
      eventCategories: Array.from(eventCategories).sort(),
      eventDays: Array.from(eventDays),
      placeCategories: Array.from(placeCategories).sort(),
    };
  };

  const filterOptions = getFilterOptions();

  // Apply filters to results
  const getFilteredResults = () => {
    if (!results) return {};

    if (activeCategory === 'all') {
      return {
        concerts: results.concerts?.slice(0, 4) || [],
        dining: results.dining?.slice(0, 4) || [],
        events: results.events?.slice(0, 4) || [],
        locations: results.locations?.slice(0, 4) || []
      };
    }

    // Apply category-specific filters (arrays - empty means all)
    if (activeCategory === 'concerts') {
      let concerts = results.concerts || [];
      if (concertFilters.genres.length > 0) {
        concerts = concerts.filter(c => concertFilters.genres.includes(c.genre));
      }
      if (concertFilters.days.length > 0) {
        concerts = concerts.filter(c => {
          if (!c.date) return false;
          const day = new Date(c.date + 'T12:00:00').toLocaleDateString('en-US', { weekday: 'short' });
          return concertFilters.days.includes(day);
        });
      }
      if (concertFilters.times.length > 0) {
        concerts = concerts.filter(c => {
          if (!c.time) return true;
          const hour = parseInt(c.time.split(':')[0]);
          const timeOfDay = hour < 18 ? 'afternoon' : 'evening';
          return concertFilters.times.includes(timeOfDay);
        });
      }
      return { concerts };
    }

    if (activeCategory === 'dining') {
      let dining = results.dining || [];
      if (diningFilters.cuisines.length > 0) {
        dining = dining.filter(d => diningFilters.cuisines.includes(d.cuisine));
      }
      if (diningFilters.prices.length > 0) {
        dining = dining.filter(d => {
          const price = d.price_level || d.price || '';
          const dollarCount = (price.match(/\$/g) || []).length;
          const priceKey = '$'.repeat(dollarCount);
          return diningFilters.prices.includes(priceKey);
        });
      }
      if (diningFilters.ratings.length > 0) {
        dining = dining.filter(d => {
          const rating = parseFloat(d.rating) || 0;
          return diningFilters.ratings.some(r => {
            if (r === '4+') return rating >= 4;
            if (r === '4.5+') return rating >= 4.5;
            return false;
          });
        });
      }
      return { dining };
    }

    if (activeCategory === 'events') {
      let events = results.events || [];
      if (eventFilters.categories.length > 0) {
        events = events.filter(e => eventFilters.categories.includes(e.category));
      }
      if (eventFilters.days.length > 0) {
        events = events.filter(e => {
          if (!e.date) return false;
          const day = new Date(e.date + 'T12:00:00').toLocaleDateString('en-US', { weekday: 'short' });
          return eventFilters.days.includes(day);
        });
      }
      return { events };
    }

    if (activeCategory === 'locations') {
      let locations = results.locations || [];
      if (placeFilters.categories.length > 0) {
        locations = locations.filter(l => placeFilters.categories.includes(l.category));
      }
      if (placeFilters.ratings.length > 0) {
        locations = locations.filter(l => {
          const rating = parseFloat(l.rating) || 0;
          return placeFilters.ratings.some(r => {
            if (r === '4+') return rating >= 4;
            if (r === '4.5+') return rating >= 4.5;
            return false;
          });
        });
      }
      return { locations };
    }

    return { [activeCategory]: results[activeCategory] || [] };
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
          /* Subscribe Tab - Coming Soon */
          <div style={{
            maxWidth: '560px',
            margin: '80px auto',
            textAlign: 'center',
          }}>
            {/* Coming Soon Banner */}
            <div style={{
              display: 'inline-block',
              padding: '8px 20px',
              background: 'linear-gradient(135deg, rgba(255,107,53,0.15) 0%, rgba(247,197,159,0.15) 100%)',
              border: '1px solid rgba(255,107,53,0.3)',
              borderRadius: '100px',
              marginBottom: '32px',
            }}>
              <span style={{
                fontSize: '13px',
                fontWeight: '600',
                letterSpacing: '0.05em',
                textTransform: 'uppercase',
                background: 'linear-gradient(135deg, #FF6B35 0%, #F7C59F 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text',
              }}>Coming Soon</span>
            </div>

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
              opacity: 0.8,
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
              marginBottom: '32px',
              lineHeight: '1.6',
            }}>
              Get personalized recommendations for concerts, restaurants, events, and hidden gems delivered every Thursday.
            </p>

            <p style={{
              fontSize: '15px',
              color: 'rgba(255,255,255,0.4)',
              lineHeight: '1.6',
            }}>
              We're putting the finishing touches on our weekly digest.<br />
              Check back soon!
            </p>

            <p style={{
              fontSize: '13px',
              color: 'rgba(255,255,255,0.3)',
              marginTop: '32px',
            }}>
              Sources: Ticketmaster • Google Places • Eater • The Infatuation • Reddit • Atlas Obscura
            </p>
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

                {searchError && (
                  <p style={{
                    fontSize: '14px',
                    color: '#F87171',
                    marginTop: '16px',
                    textAlign: 'center',
                  }}>
                    {searchError}
                  </p>
                )}

                <p style={{
                  fontSize: '12px',
                  color: 'rgba(255,255,255,0.25)',
                  marginTop: '24px',
                }}>
                  Sources: Ticketmaster • Google Places • Eater • The Infatuation • Reddit • Atlas Obscura
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
                      {results?.start_date} to {results?.end_date} • {categories[0].count} results
                    </p>
                  </div>
                  <button
                    onClick={() => { setHasResults(false); setSearchCity(''); setResults(null); setActiveCategory('all'); setWeatherData(null); setSelectedCityData(null); }}
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

                {/* Weekend Weather Bar */}
                {weatherData === 'unavailable' && (
                  <div style={{
                    marginBottom: '24px',
                    padding: '12px 20px',
                    background: 'rgba(255,255,255,0.02)',
                    borderRadius: '10px',
                    border: '1px solid rgba(255,255,255,0.04)',
                    color: 'rgba(255,255,255,0.4)',
                    fontSize: '13px',
                    textAlign: 'center',
                  }}>
                    Weather forecast not yet available for this date range
                  </div>
                )}
                {weatherData && Array.isArray(weatherData) && weatherData.length > 0 && (
                  <div style={{
                    display: 'flex',
                    gap: '8px',
                    marginBottom: '24px',
                    padding: '12px 16px',
                    background: 'rgba(255,255,255,0.03)',
                    borderRadius: '14px',
                    border: '1px solid rgba(255,255,255,0.06)',
                  }}>
                    {weatherData.map((day) => {
                      const weather = getWeatherInfo(day.weatherCode);
                      return (
                        <div
                          key={day.date}
                          style={{
                            flex: 1,
                            display: 'flex',
                            alignItems: 'center',
                            gap: '10px',
                            padding: '8px 12px',
                            borderRadius: '10px',
                          }}
                        >
                          <span style={{ fontSize: '24px' }}>{weather.icon}</span>
                          <div style={{ flex: 1 }}>
                            <div style={{
                              fontSize: '13px',
                              fontWeight: '600',
                              color: '#FAFAFA',
                              marginBottom: '2px',
                            }}>{day.dayName}</div>
                            <div style={{
                              fontSize: '11px',
                              color: 'rgba(255,255,255,0.5)',
                            }}>{weather.desc}</div>
                          </div>
                          <div style={{ textAlign: 'right' }}>
                            <div style={{
                              fontSize: '14px',
                              fontWeight: '600',
                              color: '#FAFAFA',
                            }}>{day.high}°</div>
                            <div style={{
                              fontSize: '11px',
                              color: 'rgba(255,255,255,0.4)',
                            }}>{day.low}°</div>
                          </div>
                          {day.wind > 20 && (
                            <div style={{
                              fontSize: '10px',
                              color: 'rgba(255,255,255,0.4)',
                              whiteSpace: 'nowrap',
                            }}>
                              {day.wind} mph
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}

                {/* Error Banner */}
                {results?.errors && results.errors.length > 0 && (
                  <div style={{
                    background: 'rgba(251,191,36,0.1)',
                    border: '1px solid rgba(251,191,36,0.3)',
                    borderRadius: '12px',
                    padding: '16px 20px',
                    marginBottom: '24px',
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '12px',
                  }}>
                    <span style={{ color: '#FBBF24', fontSize: '18px' }}>⚠</span>
                    <div>
                      <p style={{
                        color: '#FBBF24',
                        fontWeight: '600',
                        fontSize: '14px',
                        marginBottom: '4px'
                      }}>
                        {results.errors.some(e => e.type === 'rate_limit')
                          ? 'Some sources hit rate limits'
                          : 'Some sources unavailable'}
                      </p>
                      <p style={{ color: 'rgba(255,255,255,0.5)', fontSize: '13px' }}>
                        {results.errors.map(e => e.source).join(', ')} — results may be incomplete
                      </p>
                    </div>
                  </div>
                )}

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

                {/* Category-Specific Filters (Multiselect) */}
                {activeCategory !== 'all' && (
                  <div style={{
                    display: 'flex',
                    gap: '8px',
                    marginBottom: '32px',
                    flexWrap: 'wrap',
                    alignItems: 'center',
                  }}>
                    {/* Concert Filters */}
                    {activeCategory === 'concerts' && (
                      <>
                        {filterOptions.genres?.length > 0 && filterOptions.genres.map(genre => (
                          <button
                            key={genre}
                            onClick={() => {
                              const arr = concertFilters.genres;
                              setConcertFilters({...concertFilters, genres: arr.includes(genre) ? arr.filter(g => g !== genre) : [...arr, genre]});
                            }}
                            style={{
                              padding: '8px 16px',
                              fontSize: '12px',
                              fontWeight: '500',
                              background: concertFilters.genres.includes(genre) ? 'rgba(255,107,53,0.2)' : 'transparent',
                              border: concertFilters.genres.includes(genre) ? '1px solid rgba(255,107,53,0.5)' : '1px solid rgba(255,255,255,0.12)',
                              borderRadius: '100px',
                              color: concertFilters.genres.includes(genre) ? '#FF6B35' : 'rgba(255,255,255,0.6)',
                              cursor: 'pointer',
                              transition: 'all 0.15s',
                            }}
                          >
                            {genre}
                          </button>
                        ))}
                        {filterOptions.genres?.length > 0 && <span style={{ width: '1px', height: '20px', background: 'rgba(255,255,255,0.1)', margin: '0 4px' }} />}
                        {filterOptions.concertDays?.length > 1 && filterOptions.concertDays.map(day => (
                          <button
                            key={day}
                            onClick={() => {
                              const arr = concertFilters.days;
                              setConcertFilters({...concertFilters, days: arr.includes(day) ? arr.filter(d => d !== day) : [...arr, day]});
                            }}
                            style={{
                              padding: '8px 16px',
                              fontSize: '12px',
                              fontWeight: '500',
                              background: concertFilters.days.includes(day) ? 'rgba(255,107,53,0.2)' : 'transparent',
                              border: concertFilters.days.includes(day) ? '1px solid rgba(255,107,53,0.5)' : '1px solid rgba(255,255,255,0.12)',
                              borderRadius: '100px',
                              color: concertFilters.days.includes(day) ? '#FF6B35' : 'rgba(255,255,255,0.6)',
                              cursor: 'pointer',
                              transition: 'all 0.15s',
                            }}
                          >
                            {day}
                          </button>
                        ))}
                        {['Evening', 'Afternoon'].map(time => (
                          <button
                            key={time}
                            onClick={() => {
                              const arr = concertFilters.times;
                              const t = time.toLowerCase();
                              setConcertFilters({...concertFilters, times: arr.includes(t) ? arr.filter(x => x !== t) : [...arr, t]});
                            }}
                            style={{
                              padding: '8px 16px',
                              fontSize: '12px',
                              fontWeight: '500',
                              background: concertFilters.times.includes(time.toLowerCase()) ? 'rgba(255,107,53,0.2)' : 'transparent',
                              border: concertFilters.times.includes(time.toLowerCase()) ? '1px solid rgba(255,107,53,0.5)' : '1px solid rgba(255,255,255,0.12)',
                              borderRadius: '100px',
                              color: concertFilters.times.includes(time.toLowerCase()) ? '#FF6B35' : 'rgba(255,255,255,0.6)',
                              cursor: 'pointer',
                              transition: 'all 0.15s',
                            }}
                          >
                            {time}
                          </button>
                        ))}
                      </>
                    )}

                    {/* Dining Filters - Show all cuisine types as pills (multiselect) */}
                    {activeCategory === 'dining' && (
                      <>
                        {filterOptions.cuisines?.length > 0 && filterOptions.cuisines.map(cuisine => (
                          <button
                            key={cuisine}
                            onClick={() => {
                              const arr = diningFilters.cuisines;
                              setDiningFilters({...diningFilters, cuisines: arr.includes(cuisine) ? arr.filter(c => c !== cuisine) : [...arr, cuisine]});
                            }}
                            style={{
                              padding: '8px 16px',
                              fontSize: '12px',
                              fontWeight: '500',
                              background: diningFilters.cuisines.includes(cuisine) ? 'rgba(255,107,53,0.2)' : 'transparent',
                              border: diningFilters.cuisines.includes(cuisine) ? '1px solid rgba(255,107,53,0.5)' : '1px solid rgba(255,255,255,0.12)',
                              borderRadius: '100px',
                              color: diningFilters.cuisines.includes(cuisine) ? '#FF6B35' : 'rgba(255,255,255,0.6)',
                              cursor: 'pointer',
                              transition: 'all 0.15s',
                            }}
                          >
                            {cuisine}
                          </button>
                        ))}
                        {filterOptions.cuisines?.length > 0 && <span style={{ width: '1px', height: '20px', background: 'rgba(255,255,255,0.1)', margin: '0 4px' }} />}
                        {['$', '$$', '$$$', '$$$$'].map(price => (
                          <button
                            key={price}
                            onClick={() => {
                              const arr = diningFilters.prices;
                              setDiningFilters({...diningFilters, prices: arr.includes(price) ? arr.filter(p => p !== price) : [...arr, price]});
                            }}
                            style={{
                              padding: '8px 14px',
                              fontSize: '12px',
                              fontWeight: '500',
                              background: diningFilters.prices.includes(price) ? 'rgba(255,107,53,0.2)' : 'transparent',
                              border: diningFilters.prices.includes(price) ? '1px solid rgba(255,107,53,0.5)' : '1px solid rgba(255,255,255,0.12)',
                              borderRadius: '100px',
                              color: diningFilters.prices.includes(price) ? '#FF6B35' : 'rgba(255,255,255,0.6)',
                              cursor: 'pointer',
                              transition: 'all 0.15s',
                            }}
                          >
                            {price}
                          </button>
                        ))}
                        <span style={{ width: '1px', height: '20px', background: 'rgba(255,255,255,0.1)', margin: '0 4px' }} />
                        {['4+', '4.5+'].map(rating => (
                          <button
                            key={rating}
                            onClick={() => {
                              const arr = diningFilters.ratings;
                              setDiningFilters({...diningFilters, ratings: arr.includes(rating) ? arr.filter(r => r !== rating) : [...arr, rating]});
                            }}
                            style={{
                              padding: '8px 14px',
                              fontSize: '12px',
                              fontWeight: '500',
                              background: diningFilters.ratings.includes(rating) ? 'rgba(255,107,53,0.2)' : 'transparent',
                              border: diningFilters.ratings.includes(rating) ? '1px solid rgba(255,107,53,0.5)' : '1px solid rgba(255,255,255,0.12)',
                              borderRadius: '100px',
                              color: diningFilters.ratings.includes(rating) ? '#FF6B35' : 'rgba(255,255,255,0.6)',
                              cursor: 'pointer',
                              transition: 'all 0.15s',
                            }}
                          >
                            {rating} ★
                          </button>
                        ))}
                      </>
                    )}

                    {/* Event Filters */}
                    {activeCategory === 'events' && (
                      <>
                        {filterOptions.eventCategories?.length > 0 && filterOptions.eventCategories.map(cat => (
                          <button
                            key={cat}
                            onClick={() => {
                              const arr = eventFilters.categories;
                              setEventFilters({...eventFilters, categories: arr.includes(cat) ? arr.filter(c => c !== cat) : [...arr, cat]});
                            }}
                            style={{
                              padding: '8px 16px',
                              fontSize: '12px',
                              fontWeight: '500',
                              background: eventFilters.categories.includes(cat) ? 'rgba(255,107,53,0.2)' : 'transparent',
                              border: eventFilters.categories.includes(cat) ? '1px solid rgba(255,107,53,0.5)' : '1px solid rgba(255,255,255,0.12)',
                              borderRadius: '100px',
                              color: eventFilters.categories.includes(cat) ? '#FF6B35' : 'rgba(255,255,255,0.6)',
                              cursor: 'pointer',
                              transition: 'all 0.15s',
                            }}
                          >
                            {cat}
                          </button>
                        ))}
                        {filterOptions.eventCategories?.length > 0 && filterOptions.eventDays?.length > 1 && <span style={{ width: '1px', height: '20px', background: 'rgba(255,255,255,0.1)', margin: '0 4px' }} />}
                        {filterOptions.eventDays?.length > 1 && filterOptions.eventDays.map(day => (
                          <button
                            key={day}
                            onClick={() => {
                              const arr = eventFilters.days;
                              setEventFilters({...eventFilters, days: arr.includes(day) ? arr.filter(d => d !== day) : [...arr, day]});
                            }}
                            style={{
                              padding: '8px 16px',
                              fontSize: '12px',
                              fontWeight: '500',
                              background: eventFilters.days.includes(day) ? 'rgba(255,107,53,0.2)' : 'transparent',
                              border: eventFilters.days.includes(day) ? '1px solid rgba(255,107,53,0.5)' : '1px solid rgba(255,255,255,0.12)',
                              borderRadius: '100px',
                              color: eventFilters.days.includes(day) ? '#FF6B35' : 'rgba(255,255,255,0.6)',
                              cursor: 'pointer',
                              transition: 'all 0.15s',
                            }}
                          >
                            {day}
                          </button>
                        ))}
                      </>
                    )}

                    {/* Places Filters */}
                    {activeCategory === 'locations' && (
                      <>
                        {filterOptions.placeCategories?.length > 0 && filterOptions.placeCategories.map(cat => (
                          <button
                            key={cat}
                            onClick={() => {
                              const arr = placeFilters.categories;
                              setPlaceFilters({...placeFilters, categories: arr.includes(cat) ? arr.filter(c => c !== cat) : [...arr, cat]});
                            }}
                            style={{
                              padding: '8px 16px',
                              fontSize: '12px',
                              fontWeight: '500',
                              background: placeFilters.categories.includes(cat) ? 'rgba(255,107,53,0.2)' : 'transparent',
                              border: placeFilters.categories.includes(cat) ? '1px solid rgba(255,107,53,0.5)' : '1px solid rgba(255,255,255,0.12)',
                              borderRadius: '100px',
                              color: placeFilters.categories.includes(cat) ? '#FF6B35' : 'rgba(255,255,255,0.6)',
                              cursor: 'pointer',
                              transition: 'all 0.15s',
                            }}
                          >
                            {cat}
                          </button>
                        ))}
                        {filterOptions.placeCategories?.length > 0 && <span style={{ width: '1px', height: '20px', background: 'rgba(255,255,255,0.1)', margin: '0 4px' }} />}
                        {['4+', '4.5+'].map(rating => (
                          <button
                            key={rating}
                            onClick={() => {
                              const arr = placeFilters.ratings;
                              setPlaceFilters({...placeFilters, ratings: arr.includes(rating) ? arr.filter(r => r !== rating) : [...arr, rating]});
                            }}
                            style={{
                              padding: '8px 14px',
                              fontSize: '12px',
                              fontWeight: '500',
                              background: placeFilters.ratings.includes(rating) ? 'rgba(255,107,53,0.2)' : 'transparent',
                              border: placeFilters.ratings.includes(rating) ? '1px solid rgba(255,107,53,0.5)' : '1px solid rgba(255,255,255,0.12)',
                              borderRadius: '100px',
                              color: placeFilters.ratings.includes(rating) ? '#FF6B35' : 'rgba(255,255,255,0.6)',
                              cursor: 'pointer',
                              transition: 'all 0.15s',
                            }}
                          >
                            {rating} ★
                          </button>
                        ))}
                      </>
                    )}

                    {/* Clear Filters Button */}
                    {((activeCategory === 'concerts' && (concertFilters.genres.length > 0 || concertFilters.days.length > 0 || concertFilters.times.length > 0)) ||
                      (activeCategory === 'dining' && (diningFilters.cuisines.length > 0 || diningFilters.prices.length > 0 || diningFilters.ratings.length > 0)) ||
                      (activeCategory === 'events' && (eventFilters.categories.length > 0 || eventFilters.days.length > 0)) ||
                      (activeCategory === 'locations' && (placeFilters.categories.length > 0 || placeFilters.ratings.length > 0))) && (
                      <>
                        <span style={{ width: '1px', height: '20px', background: 'rgba(255,255,255,0.1)', margin: '0 4px' }} />
                        <button
                          onClick={() => {
                            if (activeCategory === 'concerts') setConcertFilters({ genres: [], days: [], times: [] });
                            if (activeCategory === 'dining') setDiningFilters({ cuisines: [], prices: [], ratings: [] });
                            if (activeCategory === 'events') setEventFilters({ categories: [], days: [] });
                            if (activeCategory === 'locations') setPlaceFilters({ categories: [], ratings: [] });
                          }}
                          style={{
                            padding: '8px 14px',
                            fontSize: '12px',
                            fontWeight: '500',
                            background: 'transparent',
                            border: '1px solid rgba(255,255,255,0.15)',
                            borderRadius: '100px',
                            color: 'rgba(255,255,255,0.5)',
                            cursor: 'pointer',
                            transition: 'all 0.15s',
                          }}
                        >
                          Clear
                        </button>
                      </>
                    )}
                  </div>
                )}
                
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
                          }} onClick={() => setActiveCategory('concerts')}>View all {categories.find(c => c.key === 'concerts')?.count || 0} →</button>
                        )}
                      </div>
                      <div style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
                        gap: '16px',
                      }}>
                        {filtered.concerts.map((item, idx) => {
                          // Format date with day of week
                          const formatDate = (dateStr) => {
                            if (!dateStr) return '';
                            const date = new Date(dateStr + 'T12:00:00');
                            return date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
                          };
                          const formatTime = (timeStr) => {
                            if (!timeStr) return '';
                            const [h, m] = timeStr.split(':');
                            const hour = parseInt(h);
                            const ampm = hour >= 12 ? 'PM' : 'AM';
                            const hour12 = hour % 12 || 12;
                            return `${hour12}:${m} ${ampm}`;
                          };
                          return (
                          <div key={item.name + idx} style={{
                            background: 'rgba(255,255,255,0.03)',
                            border: '1px solid rgba(255,255,255,0.06)',
                            borderRadius: '16px',
                            padding: '24px',
                            cursor: item.url ? 'pointer' : 'default',
                            transition: 'all 0.2s',
                          }}
                          onClick={() => item.url && window.open(item.url, '_blank')}
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
                                color: '#FF6B35',
                                fontWeight: '600',
                              }}>{formatDate(item.date)} • {formatTime(item.time)}</p>
                              {item.genre && (
                                <span style={{
                                  fontSize: '11px',
                                  padding: '4px 10px',
                                  background: 'rgba(255,107,53,0.15)',
                                  color: '#FF6B35',
                                  borderRadius: '100px',
                                }}>{item.genre}</span>
                              )}
                            </div>
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
                        )})}
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
                          }} onClick={() => setActiveCategory('dining')}>View all {categories.find(c => c.key === 'dining')?.count || 0} →</button>
                        )}
                      </div>
                      <div style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
                        gap: '16px',
                      }}>
                        {filtered.dining.map((item, idx) => (
                          <div key={item.name + idx} style={{
                            background: 'rgba(255,255,255,0.03)',
                            border: '1px solid rgba(255,255,255,0.06)',
                            borderRadius: '16px',
                            padding: '24px',
                            cursor: item.website || item.google_maps_url ? 'pointer' : 'default',
                            transition: 'all 0.2s',
                          }}
                          onClick={() => {
                            const url = item.website || item.google_maps_url;
                            if (url) window.open(url, '_blank');
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
                              <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                                {item.cuisine_type && (
                                  <span style={{
                                    fontSize: '11px',
                                    padding: '4px 10px',
                                    background: 'rgba(34,197,94,0.15)',
                                    color: '#22C55E',
                                    borderRadius: '100px',
                                  }}>{item.cuisine_type}</span>
                                )}
                                {item.price_level && (
                                  <span style={{
                                    fontSize: '11px',
                                    padding: '4px 10px',
                                    background: 'rgba(255,255,255,0.1)',
                                    color: 'rgba(255,255,255,0.6)',
                                    borderRadius: '100px',
                                  }}>{item.price_level}</span>
                                )}
                              </div>
                              <span style={{
                                fontSize: '12px',
                                color: 'rgba(255,255,255,0.5)',
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
                            }}>{item.neighborhood || item.address}</p>
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
                          }} onClick={() => setActiveCategory('events')}>View all {categories.find(c => c.key === 'events')?.count || 0} →</button>
                        )}
                      </div>
                      <div style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
                        gap: '16px',
                      }}>
                        {filtered.events.map((item, idx) => {
                          const formatDate = (dateStr) => {
                            if (!dateStr) return '';
                            const date = new Date(dateStr + 'T12:00:00');
                            return date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
                          };
                          const formatTime = (timeStr) => {
                            if (!timeStr) return '';
                            const [h, m] = timeStr.split(':');
                            const hour = parseInt(h);
                            const ampm = hour >= 12 ? 'PM' : 'AM';
                            const hour12 = hour % 12 || 12;
                            return `${hour12}:${m} ${ampm}`;
                          };
                          return (
                          <div key={item.name + idx} style={{
                            background: 'rgba(255,255,255,0.03)',
                            border: '1px solid rgba(255,255,255,0.06)',
                            borderRadius: '16px',
                            padding: '24px',
                            cursor: item.url ? 'pointer' : 'default',
                            transition: 'all 0.2s',
                          }}
                          onClick={() => item.url && window.open(item.url, '_blank')}
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
                              }}>{formatDate(item.date)} • {formatTime(item.time)}</p>
                              {item.category && (
                                <span style={{
                                  fontSize: '11px',
                                  padding: '4px 10px',
                                  background: 'rgba(167,139,250,0.15)',
                                  color: '#A78BFA',
                                  borderRadius: '100px',
                                }}>{item.category}</span>
                              )}
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
                        )})}
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
                          }} onClick={() => setActiveCategory('locations')}>View all {categories.find(c => c.key === 'locations')?.count || 0} →</button>
                        )}
                      </div>
                      <div style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
                        gap: '16px',
                      }}>
                        {filtered.locations.map((item, idx) => (
                          <div key={item.name + idx} style={{
                            background: 'rgba(255,255,255,0.03)',
                            border: '1px solid rgba(255,255,255,0.06)',
                            borderRadius: '16px',
                            padding: '24px',
                            cursor: (item.website || item.google_maps_url) ? 'pointer' : 'default',
                            transition: 'all 0.2s',
                          }}
                          onClick={() => {
                            const url = item.website || item.google_maps_url;
                            if (url) window.open(url, '_blank');
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
                              {item.category && (
                                <span style={{
                                  fontSize: '11px',
                                  padding: '4px 10px',
                                  background: 'rgba(56,189,248,0.15)',
                                  color: '#38BDF8',
                                  borderRadius: '100px',
                                }}>{item.category}</span>
                              )}
                              {item.rating && (
                                <span style={{
                                  fontSize: '12px',
                                  color: 'rgba(255,255,255,0.4)',
                                }}>★ {item.rating}</span>
                              )}
                            </div>
                            <h3 style={{
                              fontSize: '18px',
                              fontWeight: '600',
                              marginBottom: '8px',
                            }}>{item.name}</h3>
                            <p style={{
                              fontSize: '14px',
                              color: 'rgba(255,255,255,0.5)',
                            }}>{item.description || item.address}</p>
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
