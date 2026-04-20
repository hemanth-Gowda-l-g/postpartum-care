import React, { useEffect, useMemo, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Link, useNavigate } from 'react-router-dom';
// import QuickLog from './QuickLog'; // Keep if you want QuickLog on dashboard
// import UpcomingTasks from './UpcomingTasks'; // Keep if you want UpcomingTasks on dashboard
import Chatbot from '../components/Chatbot/Chatbot'; // Keep if you want Chatbot on dashboard
import styles from '../styles/Dashboard.module.scss';
import { Menu, MenuItem, Avatar, Typography, Divider, Box } from '@mui/material';
import dashboardBg from '../assets/illustrations/dashboard.png';
import heroOr from '../assets/illustrations/or.png';

const Dashboard = () => {
  console.log('Dashboard component rendering...'); // Log on component render
  const { currentUser } = useAuth();
  const [anchorEl, setAnchorEl] = useState(null);
  const navigate = useNavigate();
  const handleAvatarClick = (event) => {
    setAnchorEl(event.currentTarget);
  };
  const handleMenuClose = () => {
    setAnchorEl(null);
  };
  const handleProfileOpen = () => {
    navigate('/profile');
    setAnchorEl(null);
  };

  console.log('currentUser:', currentUser); // Log currentUser value

  if (!currentUser) {
    console.log('currentUser is null, showing loading message.'); // Log if showing loading
    return (
      <div className={styles.dashboardContainer}>
        <div className={styles.loadingMessage}>Loading dashboard...</div>
      </div>
    );
  }

  console.log('currentUser is available, rendering dashboard content.'); // Log if showing dashboard
  const userName = currentUser?.name || 'User';
  const userEmail = currentUser?.email || 'Not provided';

  // --- Sentiment state ---
  const [sentLoading, setSentLoading] = useState(false);
  const [sentError, setSentError] = useState(null);
  const [dailySeries, setDailySeries] = useState([]); // [{date, avg, count}]

  useEffect(() => {
    const loadSentiment = async () => {
      setSentLoading(true);
      setSentError(null);
      try {
        const token = localStorage.getItem('token');
        const res = await fetch(`/api/sentiment/timeseries?days=30`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data?.error || 'Failed to load sentiment');
        setDailySeries(Array.isArray(data?.daily) ? data.daily : []);
      } catch (e) {
        setSentError(e?.message || 'Failed to load sentiment');
      } finally {
        setSentLoading(false);
      }
    };
    loadSentiment();
  }, []);

  const last7Avg = useMemo(() => {
    if (!dailySeries?.length) return null;
    const last7 = dailySeries.slice(-7);
    if (!last7.length) return null;
    const sum = last7.reduce((s, d) => s + (Number(d.avg) || 0), 0);
    return sum / last7.length;
  }, [dailySeries]);

  const sentimentLabel = useMemo(() => {
    if (last7Avg == null) return 'N/A';
    if (last7Avg >= 0.05) return 'Positive';
    if (last7Avg <= -0.05) return 'Negative';
    return 'Neutral';
  }, [last7Avg]);

  // Build simple sparkline path (values mapped from [-1,1] to SVG height)
  const sparkPath = useMemo(() => {
    const h = 40, w = 160;
    const n = Math.max(1, dailySeries.length);
    const step = n > 1 ? w / (n - 1) : 0;
    const y = (v) => {
      const clamped = Math.max(-1, Math.min(1, Number(v) || 0));
      // map -1 -> h, 1 -> 0 (inverted y)
      return ((1 - ((clamped + 1) / 2)) * h).toFixed(2);
    };
    const x = (i) => (i * step).toFixed(2);
    const points = (dailySeries.length ? dailySeries : [{ avg: 0 }]).map((d, i) => `${x(i)},${y(d.avg)}`);
    return `M ${points.join(' L ')}`;
  }, [dailySeries]);

  const sentimentBadgeColor = useMemo(() => {
    if (sentimentLabel === 'Positive') return '#2e7d32';
    if (sentimentLabel === 'Negative') return '#c62828';
    if (sentimentLabel === 'Neutral') return '#6b7280';
    return '#9ca3af';
  }, [sentimentLabel]);

  return (
    <div className={styles.dashboardContainer}>
      {/* Removed background and overlay divs */}
      <header className={styles.dashboardHeader}> {/* New header for nav bar */}
        <div className={styles.logo}> {/* Logo and app name */}
          {/* <FaRegHeart className={styles.heartIcon} /> */}
          <span>Postpartum Care</span>
        </div>
        <nav className={styles.mainNav}> {/* Navigation links */}
          <Link to="/chat" className={styles.navLink}>Chat</Link>
          <Link to="/care-plan" className={styles.navLink}>Care Plan</Link>
          <Link to="/ppd-test" className={styles.navLink}>PPD Risk Analyzer</Link>
          <Link to="/nutrition" className={styles.navLink}>Nutrition Recommendation</Link>
          <Link to="/forum" className={styles.navLink}>Forum</Link>
          <Link to="/resources" className={styles.navLink}>Resources</Link>
          <Link to="/emergency" className={styles.navLink}>Emergency</Link>
        </nav>
        <div className={styles.userAvatar} onClick={handleAvatarClick} style={{ cursor: 'pointer' }}>
          <Avatar sx={{ bgcolor: '#6c63ff' }}>
            {userName.split(' ').map(n => n[0]).join('').toUpperCase()}
          </Avatar>
        </div>
        <Menu
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}
          onClose={handleMenuClose}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
          transformOrigin={{ vertical: 'top', horizontal: 'right' }}
        >
          <Box px={2} py={1} display="flex" alignItems="center">
            <Avatar sx={{ bgcolor: '#6c63ff', mr: 1 }}>
              {userName.split(' ').map(n => n[0]).join('').toUpperCase()}
            </Avatar>
            <Box>
              <Typography variant="subtitle1">{userName}</Typography>
              {userEmail && <Typography variant="body2" color="textSecondary">{userEmail}</Typography>}
            </Box>
          </Box>
          <Divider />
          <MenuItem onClick={handleProfileOpen}>Profile</MenuItem>
          <MenuItem onClick={handleMenuClose}>Close</MenuItem>
        </Menu>
      </header>

      <main className={styles.dashboardContent}> {/* Main content area below nav */}
        {/* Hero banner: single soft-purple card with image left and text right (placed above all) */}
        <div className={styles.heroCard}>
          <div className={styles.heroText}> 
            <div className={styles.heroKicker}>SUPPORTIVE CARE FOR NEW MOMS AND BABIES</div>
            <div className={styles.heroTitle}>Postnatal Care Application</div>
          </div>
          <div className={styles.heroPhotoWrap}>
            <img src={heroOr} alt="Mother and baby" className={styles.heroPhoto} />
          </div>
        </div>

        <h1>Welcome to your Dashboard, {userName}!</h1>
        <p>Select an option from the navigation above to get started.</p>

        {/* Sentiment widget */}
        <div className={styles.sentimentWidget} style={{
          display: 'grid',
          gridTemplateColumns: '1fr auto',
          gap: '12px',
          alignItems: 'center',
          background: '#fff',
          borderRadius: 12,
          padding: 16,
          boxShadow: '0 2px 8px rgba(0,0,0,0.05)'
        }}>
          <div>
            <h3 style={{ margin: 0 }}>Mood Trend (30 days)</h3>
            <div style={{ color: '#6b7280', fontSize: 13, marginTop: 4 }}>
              {sentLoading ? 'Loading…' : sentError ? 'Unable to load sentiment' : 'Average sentiment over time'}
            </div>
            <svg viewBox="0 0 160 40" width="160" height="40" style={{ marginTop: 8 }}>
              <path d={sparkPath} fill="none" stroke="#6c63ff" strokeWidth="2" />
              {/* zero baseline */}
              <line x1="0" y1="20" x2="160" y2="20" stroke="#e5e7eb" strokeDasharray="4 3" />
            </svg>
            <div style={{ color: '#6b7280', fontSize: 12 }}>
              Last 7-day avg: {last7Avg == null ? 'N/A' : last7Avg.toFixed(2)} (−1 to 1)
            </div>
          </div>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: 12, color: '#6b7280' }}>Current sentiment</div>
            <div style={{
              display: 'inline-block',
              marginTop: 6,
              padding: '6px 10px',
              borderRadius: 999,
              background: sentimentBadgeColor,
              color: 'white',
              fontWeight: 600
            }}>
              {sentimentLabel}
            </div>
          </div>
        </div>

        {/* Add a section for key features/cards */}
        <div className={styles.featureCards}>
          <Link to="/care-plan" className={styles.featureCardLink}>
            <div className={styles.featureCard}>
              <h3>🧠 Care Plan</h3>
              <p>Your AI-powered recovery plan</p>
            </div>
          </Link>
          <Link to="/forum" className={styles.featureCardLink}>
            <div className={styles.featureCard}>
              <h3>👥 Community Forum</h3>
              <p>Connect with other moms</p>
            </div>
          </Link>
          <Link to="/nutrition" className={styles.featureCardLink}>
            <div className={styles.featureCard}>
              <h3>🍽️ Nutrition</h3>
              <p>Track your meals</p>
            </div>
          </Link>
          <Link to="/mental-health" className={styles.featureCardLink}>
             <div className={styles.featureCard}>
              <h3>💚 Mental Health</h3>
              <p>Access support and resources</p>
            </div>
          </Link>
           {/* Add more feature cards as needed */}
        </div>

        {/* Optional: Add a dynamic tip or quote section */}
         <div className={styles.tipSection}>
          <h2>Tip of the Day</h2>
          <p>Remember to prioritize rest and seek support when you need it.</p>
         </div>

      </main>
      {/* Uncomment and position as needed */}
      <Chatbot />
    </div>
  );
};

export default Dashboard;
