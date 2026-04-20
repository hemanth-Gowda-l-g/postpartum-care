import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
  Menu,
  MenuItem,
  IconButton,
  Badge,
  Chip
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Restaurant as NutritionIcon,
  Psychology as MentalHealthIcon,
  People as PatientsIcon,
  AdminPanelSettings as AdminIcon,
  Support as SupportIcon,
  Forum as ForumIcon,
  LocalHospital as EmergencyIcon,
  Notifications as NotificationsIcon,
  AccountCircle as AccountIcon,
  ExitToApp as LogoutIcon
} from '@mui/icons-material';

const RoleBasedNavigation = ({ user, onLogout }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [anchorEl, setAnchorEl] = React.useState(null);

  const handleMenuOpen = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = () => {
    handleMenuClose();
    onLogout();
  };

  // Define navigation items based on user role
  const getNavigationItems = () => {
    const role = user?.role || 'mother';
    
    const navigationMap = {
      mother: [
        { label: 'Dashboard', path: '/dashboard', icon: <DashboardIcon /> },
        { label: 'Nutrition', path: '/nutrition', icon: <NutritionIcon /> },
        { label: 'Mental Health', path: '/mental-health', icon: <MentalHealthIcon /> },
        { label: 'PPD Test', path: '/ppd-test', icon: <MentalHealthIcon /> },
        { label: 'Chat Support', path: '/chat', icon: <SupportIcon /> },
        { label: 'Community Forum', path: '/forum', icon: <ForumIcon /> },
        { label: 'Emergency', path: '/emergency', icon: <EmergencyIcon /> }
      ],
      healthcare_provider: [
        { label: 'Dashboard', path: '/provider-dashboard', icon: <DashboardIcon /> },
        { label: 'My Patients', path: '/patients', icon: <PatientsIcon /> },
        { label: 'Clinical Tools', path: '/clinical-tools', icon: <MentalHealthIcon /> },
        { label: 'Reports', path: '/reports', icon: <DashboardIcon /> }
      ],
      mental_health_specialist: [
        { label: 'Dashboard', path: '/provider-dashboard', icon: <DashboardIcon /> },
        { label: 'My Patients', path: '/patients', icon: <PatientsIcon /> },
        { label: 'PPD Screening', path: '/ppd-tools', icon: <MentalHealthIcon /> },
        { label: 'Mental Health Plans', path: '/mental-health-plans', icon: <MentalHealthIcon /> }
      ],
      nutritionist: [
        { label: 'Dashboard', path: '/provider-dashboard', icon: <DashboardIcon /> },
        { label: 'My Patients', path: '/patients', icon: <PatientsIcon /> },
        { label: 'Nutrition Tools', path: '/nutrition-tools', icon: <NutritionIcon /> },
        { label: 'Meal Plans', path: '/meal-plans', icon: <NutritionIcon /> }
      ],
      admin: [
        { label: 'Admin Dashboard', path: '/admin-dashboard', icon: <AdminIcon /> },
        { label: 'User Management', path: '/admin/users', icon: <PatientsIcon /> },
        { label: 'Role Management', path: '/admin/roles', icon: <AdminIcon /> },
        { label: 'System Monitor', path: '/admin/system', icon: <DashboardIcon /> }
      ]
    };

    return navigationMap[role] || navigationMap.mother;
  };

  const getRoleDisplayName = () => {
    const roleNames = {
      mother: 'Patient',
      healthcare_provider: 'Healthcare Provider',
      mental_health_specialist: 'Mental Health Specialist',
      admin: 'Administrator'
    };
    return roleNames[user?.role] || 'User';
  };

  const getRoleColor = () => {
    const roleColors = {
      mother: 'primary',
      healthcare_provider: 'success',
      mental_health_specialist: 'info',
      admin: 'error'
    };
    return roleColors[user?.role] || 'primary';
  };

  const navigationItems = getNavigationItems();

  return (
    <AppBar position="static" sx={{ mb: 2 }}>
      <Toolbar>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          Postpartum Care Platform
        </Typography>

        {/* Role indicator - hidden for Patient to keep nav clean */}
        {user?.role && user.role !== 'mother' && (
          <Chip
            label={getRoleDisplayName()}
            color={getRoleColor()}
            size="small"
            sx={{ mr: 2 }}
          />
        )}

        {/* Navigation items */}
        <Box sx={{ display: { xs: 'none', md: 'flex' }, mr: 2 }}>
          {navigationItems.map((item) => (
            <Button
              key={item.path}
              color="inherit"
              startIcon={item.icon}
              onClick={() => navigate(item.path)}
              sx={{
                mx: 0.5,
                backgroundColor: location.pathname === item.path ? 'rgba(255,255,255,0.1)' : 'transparent'
              }}
            >
              {item.label}
            </Button>
          ))}
        </Box>

        {/* Notifications (for providers and admins) */}
        {['healthcare_provider', 'mental_health_specialist', 'admin'].includes(user?.role) && (
          <IconButton color="inherit" sx={{ mr: 1 }}>
            <Badge badgeContent={3} color="error">
              <NotificationsIcon />
            </Badge>
          </IconButton>
        )}

        {/* User menu */}
        <IconButton
          color="inherit"
          onClick={handleMenuOpen}
          aria-label="account menu"
        >
          <AccountIcon />
        </IconButton>
        <Menu
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}
          onClose={handleMenuClose}
          anchorOrigin={{
            vertical: 'bottom',
            horizontal: 'right',
          }}
          transformOrigin={{
            vertical: 'top',
            horizontal: 'right',
          }}
        >
          <MenuItem onClick={() => { handleMenuClose(); navigate('/profile'); }}>
            <AccountIcon sx={{ mr: 1 }} />
            Profile
          </MenuItem>
          <MenuItem onClick={handleLogout}>
            <LogoutIcon sx={{ mr: 1 }} />
            Logout
          </MenuItem>
        </Menu>
      </Toolbar>
    </AppBar>
  );
};

export default RoleBasedNavigation;
