import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Card,
  CardContent,
  Typography,
  Box,
  Alert,
  CircularProgress,
  Avatar,
  Grid,
} from '@mui/material';
import axios from 'axios';
import { AssignmentTurnedIn as CarePlanIcon, ChildCare as BreastfeedingIcon, ArrowForward as ArrowForwardIcon } from '@mui/icons-material';

// Import different dashboard components
import PatientDashboard from './PatientDashboard';
import ProviderDashboard from './ProviderDashboard';
import AdminDashboard from './AdminDashboard';
import AffirmationsDeck from './AffirmationsDeck';
import heroOr from '../../assets/illustrations/or.png';

const RoleBasedDashboard = ({ user }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [dashboardData, setDashboardData] = useState(null);
  const [bfSummary, setBfSummary] = useState(null);
  const [communityHighlights] = useState([
    { id: 1, title: 'Night feeds tips', snippet: 'How I manage cluster feeding at night…', author: 'Asha' },
    { id: 2, title: 'PPD support resources', snippet: 'Sharing what helped me during week 3…', author: 'Neha' },
    { id: 3, title: 'Pumped milk storage', snippet: 'Safe storage times and labelling hacks…', author: 'Riya' },
  ]);
  const navigate = useNavigate();

  const fetchDashboardData = useCallback(async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      if (!token) {
        setError('Authentication required');
        return;
      }

      let endpoint = '/api/dashboard/stats';
      
      // Use role-specific endpoints
      switch (user?.role) {
        case 'healthcare_provider':
        case 'mental_health_specialist':
          endpoint = '/api/provider/dashboard-stats';
          break;
        case 'admin':
          endpoint = '/api/admin/stats';
          break;
        default:
          endpoint = '/api/dashboard/stats';
      }

      const response = await axios.get(endpoint, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      setDashboardData(response.data);
      setError('');
    } catch (err) {
      console.error('Dashboard data fetch error:', err);
      setError(err.response?.data?.error || 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  }, [user]); // Add user as a dependency for useCallback

  useEffect(() => {
    fetchDashboardData();
  }, [user, fetchDashboardData]);

  // Fetch breastfeeding summary for mini-insights
  useEffect(() => {
    const fetchBf = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) return;
        const res = await axios.get('/api/breastfeeding/feed/summary', {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });
        setBfSummary(res.data || null);
      } catch (e) {
        // silent fail for dashboard
      }
    };
    fetchBf();
  }, []);

  const renderDashboardByRole = () => {
    const role = user?.role || 'mother';

    switch (role) {
      case 'mother':
        return <PatientDashboard user={user} data={dashboardData} />;
      
      case 'healthcare_provider':
      case 'mental_health_specialist':
        return <ProviderDashboard user={user} data={dashboardData} />;

      case 'admin':
        return <AdminDashboard user={user} data={dashboardData} />;
      
      default:
        return (
          <Card>
            <CardContent>
              <Typography variant="h6" color="error">
                Unknown Role
              </Typography>
              <Typography variant="body2">
                Your account role ({role}) is not recognized. Please contact support.
              </Typography>
            </CardContent>
          </Card>
        );
    }
  };

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Centered welcome heading and subtitle */}
      <Box sx={{ textAlign: 'center', mt: 1, mb: 2 }}>
        <Typography variant="h4" sx={{ fontWeight: 800, color: '#e26aa0' }}>
          Welcome to your Dashboard, {user?.name?.split(' ')[0] || 'User'}!
        </Typography>
        <Typography variant="body1" sx={{ color: '#6b7280' }}>
          Select an option from the navigation above to get started.
        </Typography>
      </Box>

      {/* Large soft-purple hero card under the title (image banner) */}
      <Box
        sx={{
          display: 'block',
          backgroundColor: '#f3eefe',
          p: { xs: 2.5, md: 3.5 },
          borderRadius: 3,
          boxShadow: '0 6px 18px rgba(0,0,0,0.08)',
          width: '100%',
          border: '1px solid rgba(108,99,255,0.15)',
          mb: 3
        }}
      >
        <Box
          component="img"
          src={heroOr}
          alt="Hero banner"
          sx={{
            width: '100%',
            height: { xs: 160, sm: 220, md: 280 },
            borderRadius: 2,
            objectFit: 'cover',
            display: 'block',
            boxShadow: 1,
          }}
        />
      </Box>
      {/* Daily Affirmations + Key cards row */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} md={5}>
          <AffirmationsDeck />
        </Grid>
        <Grid item xs={12} md={7}>
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' }, gap: 2 }}>
            <Card sx={{ cursor: 'pointer', '&:hover': { boxShadow: 4 } }} onClick={() => navigate('/care-plan')}>
              <CardContent>
                <Box display="flex" alignItems="center" gap={1.5}>
                  <Avatar sx={{ bgcolor: 'rgba(147,197,253,0.35)', color: '#1e40af' }}>
                    <CarePlanIcon />
                  </Avatar>
                  <Box>
                    <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>Care Plan</Typography>
                    <Typography variant="caption" color="text.secondary">View your weekly plan</Typography>
                  </Box>
                </Box>
                <Box sx={{ mt: 1.5, display: 'flex', alignItems: 'center', color: 'primary.main' }}>
                  <Typography variant="body2" sx={{ mr: 0.5 }}>Open</Typography>
                  <ArrowForwardIcon fontSize="small" />
                </Box>
              </CardContent>
            </Card>
            <Card sx={{ cursor: 'pointer', '&:hover': { boxShadow: 4 } }} onClick={() => navigate('/breastfeeding')}>
              <CardContent>
                <Box display="flex" alignItems="center" gap={1.5}>
                  <Avatar sx={{ bgcolor: 'rgba(186,230,253,0.35)', color: '#075985' }}>
                    <BreastfeedingIcon />
                  </Avatar>
                  <Box>
                    <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>Breastfeeding</Typography>
                    <Typography variant="caption" color="text.secondary">Latest session summary</Typography>
                  </Box>
                </Box>
                {bfSummary && (
                  <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1 }}>
                    Feeds: <strong>{bfSummary.count || 0}</strong> | Total: <strong>{Math.round((bfSummary.total_duration_sec||0)/60)} mins</strong>
                    {bfSummary.next_feed_in_min ? (
                      <> | Next feed in <strong>{bfSummary.next_feed_in_min}</strong> mins</>
                    ) : null}
                  </Typography>
                )}
                <Box sx={{ mt: 1.5, display: 'flex', alignItems: 'center', color: 'primary.main' }}>
                  <Typography variant="body2" sx={{ mr: 0.5 }}>Open</Typography>
                  <ArrowForwardIcon fontSize="small" />
                </Box>
              </CardContent>
            </Card>
          </Box>
        </Grid>
        {/* Hero card moved above; removed from here */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="subtitle1" gutterBottom>You’re not alone — top discussions</Typography>
              <Box display="flex" gap={2} sx={{ overflowX: 'auto' }}>
                {communityHighlights.map((p) => (
                  <Box key={p.id} sx={{ minWidth: 180, p: 1.5, borderRadius: 2, bgcolor: 'rgba(147,197,253,0.15)' }}>
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>{p.title}</Typography>
                    <Typography variant="caption" color="text.secondary">{p.snippet}</Typography>
                    <Typography variant="caption" display="block" sx={{ mt: 0.5 }}>by {p.author}</Typography>
                  </Box>
                ))}
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {renderDashboardByRole()}
    </Container>
  );
};

export default RoleBasedDashboard;
