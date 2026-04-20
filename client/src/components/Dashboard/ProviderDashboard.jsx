import React from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Avatar,
  Chip,
  Button,
  Alert
} from '@mui/material';
import {
  People as PeopleIcon,
  TrendingUp as TrendingUpIcon,
  Warning as WarningIcon,
  Assignment as AssignmentIcon,
  Person as PersonIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

const ProviderDashboard = ({ user, data }) => {
  const navigate = useNavigate();

  const getProviderTypeLabel = () => {
    const labels = {
      healthcare_provider: 'Healthcare Provider',
      mental_health_specialist: 'Mental Health Specialist'
    };
    return labels[user?.role] || 'Provider';
  };

  const getProviderColor = () => {
    const colors = {
      healthcare_provider: 'success',
      mental_health_specialist: 'info'
    };
    return colors[user?.role] || 'primary';
  };

  return (
    <Grid container spacing={3}>
      {/* Provider Info Card */}
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Box display="flex" alignItems="center" justifyContent="space-between">
              <Box>
                <Typography variant="h5" gutterBottom>
                  {getProviderTypeLabel()} Dashboard
                </Typography>
                <Chip 
                  label={getProviderTypeLabel()} 
                  color={getProviderColor()} 
                  size="small" 
                />
              </Box>
              <Button
                variant="contained"
                onClick={() => navigate('/patients')}
                startIcon={<PeopleIcon />}
              >
                View All Patients
              </Button>
            </Box>
          </CardContent>
        </Card>
      </Grid>

      {/* Stats Cards */}
      <Grid item xs={12} sm={6} md={3}>
        <Card>
          <CardContent>
            <Box display="flex" alignItems="center">
              <Avatar sx={{ bgcolor: 'primary.main', mr: 2 }}>
                <PeopleIcon />
              </Avatar>
              <Box>
                <Typography variant="h4">
                  {data?.total_patients || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Total Patients
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
                <TrendingUpIcon />
              </Avatar>
              <Box>
                <Typography variant="h4">
                  {data?.recent_checkins || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Recent Check-ins
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
                <WarningIcon />
              </Avatar>
              <Box>
                <Typography variant="h4">
                  {data?.alerts_count || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Active Alerts
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
                <AssignmentIcon />
              </Avatar>
              <Box>
                <Typography variant="h4">
                  {data?.care_plans || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Active Care Plans
                </Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>
      </Grid>

      {/* High Risk Patients Alert */}
      {data?.high_risk_patients && data.high_risk_patients.length > 0 && (
        <Grid item xs={12}>
          <Alert severity="warning" sx={{ mb: 2 }}>
            <Typography variant="h6" gutterBottom>
              Patients Requiring Attention
            </Typography>
            <Typography variant="body2">
              {data.high_risk_patients.length} patient(s) have concerning indicators that may require immediate attention.
            </Typography>
          </Alert>
        </Grid>
      )}

      {/* High Risk Patients List */}
      {data?.high_risk_patients && data.high_risk_patients.length > 0 && (
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Patients Requiring Attention
              </Typography>
              <List>
                {data.high_risk_patients.slice(0, 5).map((patient, index) => (
                  <ListItem 
                    key={index}
                    button
                    onClick={() => navigate(`/patients/${patient.patient_id}`)}
                  >
                    <ListItemAvatar>
                      <Avatar>
                        <PersonIcon />
                      </Avatar>
                    </ListItemAvatar>
                    <ListItemText
                      primary={patient.patient_name}
                      secondary={`Average mood: ${patient.avg_mood}/5`}
                    />
                    <Chip 
                      label="Low Mood" 
                      color="warning" 
                      size="small" 
                    />
                  </ListItem>
                ))}
              </List>
              {data.high_risk_patients.length > 5 && (
                <Button 
                  fullWidth 
                  onClick={() => navigate('/patients?filter=high_risk')}
                >
                  View All ({data.high_risk_patients.length})
                </Button>
              )}
            </CardContent>
          </Card>
        </Grid>
      )}

      {/* Quick Actions */}
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Quick Actions
            </Typography>
            <Box display="flex" flexDirection="column" gap={2}>
              <Button
                variant="outlined"
                fullWidth
                onClick={() => navigate('/patients')}
                startIcon={<PeopleIcon />}
              >
                View All Patients
              </Button>
              
              {user?.role === 'mental_health_specialist' && (
                <Button
                  variant="outlined"
                  fullWidth
                  onClick={() => navigate('/ppd-screening')}
                  startIcon={<AssignmentIcon />}
                >
                  PPD Screening Tools
                </Button>
              )}
              
              <Button
                variant="outlined"
                fullWidth
                onClick={() => navigate('/reports')}
                startIcon={<TrendingUpIcon />}
              >
                Generate Reports
              </Button>
            </Box>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );
};

export default ProviderDashboard;
