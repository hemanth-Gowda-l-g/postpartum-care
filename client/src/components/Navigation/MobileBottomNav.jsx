import React from 'react';
import { BottomNavigation, BottomNavigationAction, Paper } from '@mui/material';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  Home as HomeIcon,
  Restaurant as NutritionIcon,
  Psychology as MentalHealthIcon,
  ChildCare as BreastfeedingIcon,
  Forum as ForumIcon
} from '@mui/icons-material';

const navItems = [
  { label: 'Dashboard', path: '/dashboard', icon: <HomeIcon /> },
  { label: 'Nutrition', path: '/nutrition', icon: <NutritionIcon /> },
  { label: 'Mental', path: '/mental-health', icon: <MentalHealthIcon /> },
  { label: 'Breastfeed', path: '/breastfeeding', icon: <BreastfeedingIcon /> },
  { label: 'Forum', path: '/forum', icon: <ForumIcon /> },
];

const MobileBottomNav = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const currentIndex = Math.max(0, navItems.findIndex(i => location.pathname.startsWith(i.path)));

  return (
    <Paper
      sx={{ position: 'fixed', bottom: 0, left: 0, right: 0, display: { xs: 'block', md: 'none' }, zIndex: 1400 }}
      elevation={3}
    >
      <BottomNavigation
        showLabels
        value={currentIndex}
        onChange={(e, newValue) => navigate(navItems[newValue].path)}
      >
        {navItems.map(item => (
          <BottomNavigationAction key={item.path} label={item.label} icon={item.icon} />
        ))}
      </BottomNavigation>
    </Paper>
  );
};

export default MobileBottomNav;
