import React from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Avatar,
  Button
} from '@mui/material';
import {
  Support as SupportIcon,
  People as PeopleIcon,
  Help as HelpIcon,
  Analytics as AnalyticsIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

const SupportDashboard = ({ user, data }) => {
  const navigate = useNavigate();

  return (
    <Grid container spacing={3}>
      {/* Support Header */}
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Typography variant="h5" gutterBottom>
              Support Dashboard
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Assist users and provide technical support for the platform.
            </Typography>
          </CardContent>
        </Card>
      </Grid>

      {/* Support Stats */}
      <Grid item xs={12} sm={6} md={3}>
        <Card>
          <CardContent>
            <Box display="flex" alignItems="center">
              <Avatar sx={{ bgcolor: 'primary.main', mr: 2 }}>
                <SupportIcon />
              </Avatar>
              <Box>
                <Typography variant="h4">
                  {data?.open_tickets || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Open Tickets
                </Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} sm={6} md={3}>
        <Card>
          <CardContent>
            <Box display="flex" alignItems="center">
              <Avatar sx={{ bgcolor: 'success.main', mr: 2 }}>
                <PeopleIcon />
              </Avatar>
              <Box>
                <Typography variant="h4">
                  {data?.users_helped || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Users Helped Today
                </Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} sm={6} md={3}>
        <Card>
          <CardContent>
            <Box display="flex" alignItems="center">
              <Avatar sx={{ bgcolor: 'info.main', mr: 2 }}>
                <HelpIcon />
              </Avatar>
              <Box>
                <Typography variant="h4">
                  {data?.avg_response_time || '2h'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Avg Response Time
                </Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} sm={6} md={3}>
        <Card>
          <CardContent>
            <Box display="flex" alignItems="center">
              <Avatar sx={{ bgcolor: 'warning.main', mr: 2 }}>
                <AnalyticsIcon />
              </Avatar>
              <Box>
                <Typography variant="h4">
                  {data?.satisfaction_rate || '95%'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Satisfaction Rate
                </Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>
      </Grid>

      {/* Quick Actions */}
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Quick Actions
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6} md={3}>
                <Button
                  variant="outlined"
                  fullWidth
                  onClick={() => navigate('/support/tickets')}
                  startIcon={<SupportIcon />}
                >
                  View Tickets
                </Button>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Button
                  variant="outlined"
                  fullWidth
                  onClick={() => navigate('/support/users')}
                  startIcon={<PeopleIcon />}
                >
                  User Support
                </Button>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Button
                  variant="outlined"
                  fullWidth
                  onClick={() => navigate('/support/knowledge-base')}
                  startIcon={<HelpIcon />}
                >
                  Knowledge Base
                </Button>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Button
                  variant="outlined"
                  fullWidth
                  onClick={() => navigate('/support/analytics')}
                  startIcon={<AnalyticsIcon />}
                >
                  Support Analytics
                </Button>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );
};

export default SupportDashboard;
