import React from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Avatar
} from '@mui/material';
import {
  Restaurant as NutritionIcon,
  Psychology as MentalHealthIcon,
  Forum as ForumIcon,
  LocalHospital as EmergencyIcon,
  Assignment as PlanIcon,
  ChildCare as BreastfeedingIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import WellnessWheel from './WellnessWheel';

const PatientDashboard = ({ user, data }) => {
  const navigate = useNavigate();

  return (
    <Grid container spacing={3}>

      {/* Feature Cards */}
      <Grid item xs={12} sm={6} md={3}>
        <Card sx={{ borderRadius: 3, minHeight: 140, '&:hover': { boxShadow: 3 }, cursor: 'pointer' }} onClick={() => navigate('/nutrition')}>
          <CardContent>
            <Box display="flex" alignItems="center">
              <Avatar sx={{ bgcolor: 'rgba(255,199,162,0.7)', color: '#b85c00', mr: 2 }}>
                <NutritionIcon />
              </Avatar>
              <Box>
                <Typography variant="h6">
                  Nutrition
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Track your meals
                </Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} sm={6} md={3}>
        <Card sx={{ borderRadius: 3, minHeight: 140, '&:hover': { boxShadow: 3 }, cursor: 'pointer' }} onClick={() => navigate('/mental-health')}>
          <CardContent>
            <Box display="flex" alignItems="center">
              <Avatar sx={{ bgcolor: 'rgba(134,239,172,0.7)', color: '#166534', mr: 2 }}>
                <MentalHealthIcon />
              </Avatar>
              <Box>
                <Typography variant="h6">
                  Mental Health
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Daily check-ins
                </Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} sm={6} md={3}>
        <Card sx={{ borderRadius: 3, minHeight: 140, cursor: 'pointer', '&:hover': { boxShadow: 3 } }} onClick={() => navigate('/forum')}>
          <CardContent>
            <Box display="flex" alignItems="center">
              <Avatar sx={{ bgcolor: 'rgba(147,197,253,0.7)', color: '#1e40af', mr: 2 }}>
                <ForumIcon />
              </Avatar>
              <Box>
                <Typography variant="h6">
                  Community Forum
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Connect with other moms
                </Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} sm={6} md={3}>
        <Card sx={{ borderRadius: 3, minHeight: 140, cursor: 'pointer', '&:hover': { boxShadow: 3 } }} onClick={() => navigate('/emergency')}>
          <CardContent>
            <Box display="flex" alignItems="center">
              <Avatar sx={{ bgcolor: 'rgba(254,202,202,0.9)', color: '#b91c1c', mr: 2 }}>
                <EmergencyIcon />
              </Avatar>
              <Box>
                <Typography variant="h6">
                  Emergency
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  India emergency contacts
                </Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} sm={6} md={3}>
        <Card 
          sx={{ borderRadius: 3, minHeight: 140, cursor: 'pointer', '&:hover': { boxShadow: 3 }}}
          onClick={() => navigate('/care-plan')}
        >
          <CardContent>
            <Box display="flex" alignItems="center">
              <Avatar sx={{ bgcolor: 'rgba(255,237,213,0.9)', color: '#92400e', mr: 2 }}>
                <PlanIcon />
              </Avatar>
              <Box>
                <Typography variant="h6">
                  Care Plan
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Your AI-powered recovery plan
                </Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>
      </Grid>

      {/* Breastfeeding Card */}
      <Grid item xs={12} sm={6} md={3}>
        <Card 
          sx={{ borderRadius: 3, minHeight: 140, cursor: 'pointer', '&:hover': { boxShadow: 3 } }}
          onClick={() => navigate('/breastfeeding')}
        >
          <CardContent>
            <Box display="flex" alignItems="center">
              <Avatar sx={{ bgcolor: 'rgba(183,148,244,0.7)', color: '#5b21b6', mr: 2 }}>
                <BreastfeedingIcon />
              </Avatar>
              <Box>
                <Typography variant="h6">
                  Breastfeeding
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Track feeds and insights
                </Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>
      </Grid>

      {/* Wellness Wheel */}
      <Grid item xs={12} md={12}>
        <WellnessWheel />
      </Grid>

      
    </Grid>
  );
};

export default PatientDashboard;
