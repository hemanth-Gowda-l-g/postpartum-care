import React from 'react';
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import RoleBasedNavigation from './components/Navigation/RoleBasedNavigation';
import RoleBasedDashboard from './components/Dashboard/RoleBasedDashboard';
import Login from './components/Auth/Login';
import Signup from './components/Auth/Signup';
import Onboarding from './pages/Onboarding';
import RecoveryPlan from './pages/RecoveryPlan';
import MentalHealth from './pages/MentalHealth';
import QuickLog from './pages/QuickLog';
import PPDTestPage from './pages/PPDTestPage';
import CarePlan from './pages/CarePlan';
import NutritionPrediction from './components/Nutrition/NutritionPrediction';
import MLDashboard from './components/MLDashboard';
import ChatPage from './pages/ChatPage';
import Forum from './pages/Forum';
import Resources from './pages/Resources';
import Emergency from './pages/Emergency';
import Profile from './pages/Profile';
// Removed Progress/UpcomingTasks route
import BreastfeedingTracker from './pages/BreastfeedingTracker';
import { Container, Box, Fab, Tooltip, SpeedDial, SpeedDialAction, SpeedDialIcon } from '@mui/material';
import MedicalInformationIcon from '@mui/icons-material/MedicalInformation';
import MobileBottomNav from './components/Navigation/MobileBottomNav';
import SupportAgentIcon from '@mui/icons-material/SupportAgent';
import PsychologyIcon from '@mui/icons-material/Psychology';
import ChildCareIcon from '@mui/icons-material/ChildCare';
import './styles/globals.scss';
import './styles/App.scss';

const PrivateRoute = ({ children, roles = [] }) => { // UPDATED TO HANDLE ROLES
  const { currentUser } = useAuth();
  
  // Check if user is logged in
  if (!currentUser) return <Navigate to="/login" />;
  
  // Check if route requires specific roles
  if (roles.length > 0 && !roles.includes(currentUser.role)) {
    return <Navigate to="/dashboard" />; // Redirect if not authorized
  }
  
  return children;
};

function App() {
  const { currentUser, logout, loading } = useAuth();
  const navigate = useNavigate();

  if (loading) {
    return (
      <Container maxWidth="lg">
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh">
          Loading...
        </Box>
      </Container>
    );
  }

  // Show login/signup pages without navigation
  const isAuthPage = window.location.pathname === '/login' || window.location.pathname === '/signup';

  return (
    <div>
      {/* Show navigation only when user is logged in and not on auth pages */}
      {currentUser && !isAuthPage && (
        <RoleBasedNavigation user={currentUser} onLogout={logout} />
      )}

      <Container maxWidth="lg" sx={{ mt: isAuthPage ? 0 : 2, pb: { xs: 8, md: 0 } }}>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />

          {/* Protected routes */}
          <Route
            path="/dashboard"
            element={
              <PrivateRoute>
                <RoleBasedDashboard user={currentUser} />
              </PrivateRoute>
            }
          />
          <Route
            path="/provider-dashboard"
            element={
              <PrivateRoute roles={['healthcare_provider', 'mental_health_specialist']}>
                <RoleBasedDashboard user={currentUser} />
              </PrivateRoute>
            }
          />
          <Route
            path="/admin-dashboard"
            element={
              <PrivateRoute roles={['admin']}>
                <RoleBasedDashboard user={currentUser} />
              </PrivateRoute>
            }
          />
          <Route
            path="/ppd-test"
            element={
              <PrivateRoute>
                <PPDTestPage />
              </PrivateRoute>
            }
          />
          <Route
            path="/care-plan"
            element={
              <PrivateRoute>
                <CarePlan />
              </PrivateRoute>
            }
          />
          <Route
            path="/onboarding"
            element={
              <PrivateRoute>
                <Onboarding />
              </PrivateRoute>
            }
          />
          <Route
            path="/recovery-plan"
            element={
              <PrivateRoute>
                <RecoveryPlan />
              </PrivateRoute>
            }
          />
          <Route
            path="/mental-health"
            element={
              <PrivateRoute>
                <MentalHealth />
              </PrivateRoute>
            }
          />
          <Route
            path="/quick-log"
            element={
              <PrivateRoute>
                <QuickLog />
              </PrivateRoute>
            }
          />
          <Route
            path="/nutrition"
            element={
              <PrivateRoute>
                <NutritionPrediction />
              </PrivateRoute>
            }
          />
          <Route
            path="/breastfeeding"
            element={
              <PrivateRoute>
                <BreastfeedingTracker />
              </PrivateRoute>
            }
          />
          <Route
            path="/ml-dashboard"
            element={
              <PrivateRoute roles={['admin']}>
                <MLDashboard />
              </PrivateRoute>
            }
          />
          <Route
            path="/chat"
            element={
              <PrivateRoute>
                <ChatPage />
              </PrivateRoute>
            }
          />
          <Route
            path="/forum"
            element={
              <PrivateRoute>
                <Forum />
              </PrivateRoute>
            }
          />
          <Route
            path="/resources"
            element={
              <PrivateRoute>
                <Resources />
              </PrivateRoute>
            }
          />
          <Route
            path="/emergency"
            element={
              <PrivateRoute>
                <Emergency />
              </PrivateRoute>
            }
          />
          <Route
            path="/profile"
            element={
              <PrivateRoute>
                <Profile />
              </PrivateRoute>
            }
          />
          {/** Progress route removed in favor of Community Forum */}

          {/* Default route */}
          <Route path="/" element={<Navigate to={currentUser ? "/dashboard" : "/login"} />} />
        </Routes>
      </Container>

      {/* Ask the Expert SpeedDial */}
      {currentUser && !isAuthPage && (
        <SpeedDial
          ariaLabel="Ask the Expert"
          sx={{ position: 'fixed', bottom: { xs: 210, md: 168 }, right: 24, zIndex: 1500 }}
          icon={<SpeedDialIcon openIcon={<SupportAgentIcon />} />}
        >
          <SpeedDialAction
            key="OB-GYN"
            icon={<SupportAgentIcon />}
            tooltipTitle="OB-GYN"
            onClick={() => navigate('/chat?topic=obgyn')}
          />
          <SpeedDialAction
            key="Psychologist"
            icon={<PsychologyIcon />}
            tooltipTitle="Psychologist"
            onClick={() => navigate('/chat?topic=psychology')}
          />
          <SpeedDialAction
            key="Lactation"
            icon={<ChildCareIcon />}
            tooltipTitle="Lactation"
            onClick={() => navigate('/chat?topic=lactation')}
          />
        </SpeedDial>
      )}

      {/* Emergency Floating Action Button */}
      {currentUser && !isAuthPage && (
        <Tooltip title="Emergency Help (India: 112)" placement="left">
          <Fab
            color="error"
            aria-label="emergency"
            href="tel:112"
            sx={{ position: 'fixed', bottom: { xs: 138, md: 96 }, right: 24, zIndex: 1400 }}
          >
            <MedicalInformationIcon />
          </Fab>
        </Tooltip>
      )}

      {/* Mobile bottom navigation */}
      {currentUser && !isAuthPage && (
        <MobileBottomNav />
      )}
    </div>
  );
}

export default App;
