import React from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Avatar,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import {
  People as PeopleIcon,
  Security as SecurityIcon,
  Analytics as AnalyticsIcon,
  Settings as SettingsIcon,
  AdminPanelSettings as AdminIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

const AdminDashboard = ({ user, data }) => {
  const navigate = useNavigate();

  return (
    <Grid container spacing={3}>
      {/* Admin Header */}
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Box display="flex" alignItems="center" justifyContent="space-between">
              <Box>
                <Typography variant="h5" gutterBottom>
                  Administrator Dashboard
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  System overview and management tools
                </Typography>
              </Box>
              <Button
                variant="contained"
                color="error"
                onClick={() => navigate('/admin/users')}
                startIcon={<AdminIcon />}
              >
                Manage Users
              </Button>
            </Box>
          </CardContent>
        </Card>
      </Grid>

      {/* System Stats */}
      <Grid item xs={12} sm={6} md={3}>
        <Card>
          <CardContent>
            <Box display="flex" alignItems="center">
              <Avatar sx={{ bgcolor: 'primary.main', mr: 2 }}>
                <PeopleIcon />
              </Avatar>
              <Box>
                <Typography variant="h4">
                  {data?.users?.total_users || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Total Users
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
                <AnalyticsIcon />
              </Avatar>
              <Box>
                <Typography variant="h4">
                  {data?.assignments?.total_assignments || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Active Assignments
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
                <SecurityIcon />
              </Avatar>
              <Box>
                <Typography variant="h4">
                  {data?.platform_usage?.nutrition_profiles || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Nutrition Profiles
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
                <SettingsIcon />
              </Avatar>
              <Box>
                <Typography variant="h4">
                  {data?.platform_usage?.daily_checkins || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Daily Check-ins
                </Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>
      </Grid>

      {/* User Distribution by Role */}
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              User Distribution by Role
            </Typography>
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Role</TableCell>
                    <TableCell align="right">Count</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {data?.users?.by_role && Object.entries(data.users.by_role).map(([role, count]) => (
                    <TableRow key={role}>
                      <TableCell component="th" scope="row">
                        {role.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </TableCell>
                      <TableCell align="right">{count}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      </Grid>

      {/* Assignment Statistics */}
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Assignment Statistics
            </Typography>
            <Box sx={{ mt: 2 }}>
              <Typography variant="body2" gutterBottom>
                Patients with Providers: {data?.assignments?.patients_with_providers || 0}
              </Typography>
              <Typography variant="body2" gutterBottom>
                Providers with Patients: {data?.assignments?.providers_with_patients || 0}
              </Typography>
              {data?.assignments?.assignment_types && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Assignment Types:
                  </Typography>
                  {Object.entries(data.assignments.assignment_types).map(([type, count]) => (
                    <Typography key={type} variant="body2">
                      {type}: {count}
                    </Typography>
                  ))}
                </Box>
              )}
            </Box>
          </CardContent>
        </Card>
      </Grid>

      {/* Quick Admin Actions */}
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
                  onClick={() => navigate('/admin/users')}
                  startIcon={<PeopleIcon />}
                >
                  Manage Users
                </Button>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Button
                  variant="outlined"
                  fullWidth
                  onClick={() => navigate('/admin/roles')}
                  startIcon={<SecurityIcon />}
                >
                  Manage Roles
                </Button>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Button
                  variant="outlined"
                  fullWidth
                  onClick={() => navigate('/admin/assignments')}
                  startIcon={<AnalyticsIcon />}
                >
                  Manage Assignments
                </Button>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Button
                  variant="outlined"
                  fullWidth
                  onClick={() => navigate('/admin/system')}
                  startIcon={<SettingsIcon />}
                >
                  System Settings
                </Button>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );
};

export default AdminDashboard;
