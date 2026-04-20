import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Box,
  Typography,
  Paper,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Stepper,
  Step,
  StepLabel,
  Card,
  CardContent,
  Chip,
  LinearProgress,
  Alert,
  CircularProgress,
  Checkbox,
  Grid,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  IconButton
} from '@mui/material';
import {
  Psychology,
  Refresh,
  LocalHospital
} from '@mui/icons-material';
import styles from '../styles/CarePlan.module.scss';

const CarePlan = () => {
  const { currentUser } = useAuth();
  const navigate = useNavigate();
  
  // State management
  const [activeStep, setActiveStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  // Form data (restore from localStorage if available)
  const savedForm = (() => {
    try {
      const raw = localStorage.getItem('carePlanFormData');
      return raw ? JSON.parse(raw) : null;
    } catch (e) {
      return null;
    }
  })();

  const [formData, setFormData] = useState(
    savedForm || {
      delivery_date: '',
      delivery_type: '',
      feeding: '',
      specific_concerns: '',
      postpartum_week: '',
      epds_score: '',
      ppd_risk_percentage: null
    }
  );
  
  // Care plan data
  const [carePlan, setCarePlan] = useState(null);
  const [existingPPDScore, setExistingPPDScore] = useState(null);
  const [loadingPPD, setLoadingPPD] = useState(false);

  const steps = ['Assessment', 'Generate Plan', 'Your Care Plan'];

  const deliveryTypes = [
    { value: 'vaginal', label: 'Vaginal Birth' },
    { value: 'c_section', label: 'C-Section' },
    { value: 'assisted', label: 'Assisted Delivery (Forceps/Vacuum)' }
  ];

  const feedingTypes = [
    { value: 'breastfeeding', label: 'Breastfeeding Only' },
    { value: 'formula', label: 'Formula Only' },
    { value: 'mixed', label: 'Mixed Feeding' }
  ];

  const commonConcerns = [
    'Severe fatigue',
    'Mood swings',
    'Low milk supply',
    'Pain while feeding',
    'Incision pain',
    'Back pain',
    'Sleep deprivation',
    'No family support',
    'Feeling overwhelmed',
    'Worried about scar healing'
  ];

  const loadExistingPPDScore = useCallback(async () => {
    try {
      setLoadingPPD(true);
      const response = await api.get(`/ppd/latest-score/${currentUser.uid || currentUser.id || currentUser._id}`);
      if (response.data.success && response.data.score !== null) {
        setExistingPPDScore(response.data.score);
        // Convert percentage to EPDS score for compatibility
        const epdsScore = Math.round(response.data.score * 0.27); // Convert 0-100% to 0-27 EPDS scale
        setFormData(prev => ({ 
          ...prev, 
          epds_score: epdsScore,
          ppd_risk_percentage: response.data.score 
        }));
        setSuccess(`Found your recent PPD assessment: ${response.data.score}% risk!`);
      }
    } catch (error) {
      console.log('No existing PPD score found');
    } finally {
      setLoadingPPD(false);
    }
  }, [currentUser.uid, currentUser.id, currentUser._id]);

  const loadExistingCarePlan = useCallback(async () => {
    // Removed automatic care plan loading - always start with assessment
    console.log('Care plan loading disabled - user must complete assessment');
  }, []);

  // Load existing PPD score on component mount
  useEffect(() => {
    if (currentUser) {
      loadExistingPPDScore();
      loadExistingCarePlan();
    }
  }, [currentUser, loadExistingPPDScore, loadExistingCarePlan]);

  // Persist form data to localStorage on change
  useEffect(() => {
    try {
      localStorage.setItem('carePlanFormData', JSON.stringify(formData));
    } catch (e) {
      // ignore quota errors
    }
  }, [formData]);

  // Read ppdRisk from route state (coming from PPDTestPage) and merge
  const location = useLocation();
  useEffect(() => {
    if (location.state && typeof location.state.ppdRisk === 'number') {
      const ppdRisk = location.state.ppdRisk;
      const epdsScore = Math.round(ppdRisk * 0.27);
      setFormData(prev => ({
        ...prev,
        epds_score: epdsScore,
        ppd_risk_percentage: ppdRisk
      }));
      setExistingPPDScore(ppdRisk);
    }
    // If delivery_date is present but postpartum_week empty, compute it
    if (formData.delivery_date && !formData.postpartum_week) {
      const week = calculatePostpartumWeek(formData.delivery_date);
      setFormData(prev => ({ ...prev, postpartum_week: week }));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    setError('');
  };

  const calculatePostpartumWeek = (deliveryDate) => {
    const delivery = new Date(deliveryDate);
    const today = new Date();
    const diffTime = Math.abs(today - delivery);
    const diffWeeks = Math.ceil(diffTime / (1000 * 60 * 60 * 24 * 7));
    return Math.max(1, diffWeeks);
  };

  const handleDeliveryDateChange = (date) => {
    handleInputChange('delivery_date', date);
    if (date) {
      const week = calculatePostpartumWeek(date);
      handleInputChange('postpartum_week', week);
    }
  };

  const validateStep = (step) => {
    switch (step) {
      case 0:
        if (!formData.delivery_date || !formData.delivery_type || !formData.feeding || !formData.specific_concerns) {
          setError('Please fill in all required fields');
          return false;
        }
        if (!formData.epds_score && formData.epds_score !== 0) {
          setError('PPD assessment score is required. Please take the PPD test first or enter your score manually.');
          return false;
        }
        return true;
      default:
        return true;
    }
  };

  const handleNext = () => {
    if (validateStep(activeStep)) {
      setActiveStep(prev => prev + 1);
      if (activeStep === 0) {
        generateCarePlan();
      }
    }
  };

  const handleBack = () => {
    setActiveStep(prev => prev - 1);
  };

  const takePPDTest = () => {
    navigate('/ppd-test');
  };

  const generateCarePlan = async () => {
    try {
      setLoading(true);
      setError('');

      const planData = {
        user_id: currentUser.uid || currentUser.id || currentUser._id,
        epds_score: formData.epds_score,
        ppd_risk_percentage: formData.ppd_risk_percentage,
        postpartum_week: formData.postpartum_week,
        delivery_type: formData.delivery_type,
        feeding: formData.feeding,
        specific_concerns: formData.specific_concerns,
        delivery_date: formData.delivery_date
      };

      const response = await api.post('/care-plan/generate', planData);
      
      if (response.data.success) {
        setCarePlan(response.data.care_plan);
        setSuccess('Your personalized care plan has been generated using ML clustering!');
        setActiveStep(2);
        // Clear saved draft after successful generation
        try { localStorage.removeItem('carePlanFormData'); } catch (e) {}
      } else {
        setError(response.data.error || 'Failed to generate care plan');
      }
    } catch (error) {
      setError('Error generating care plan. Please try again.');
      console.error('Care plan generation error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleTaskCompletion = async (taskId, completed) => {
    try {
      const response = await api.put('/care-plan/task/complete', {
        care_plan_id: carePlan.id || carePlan._id,
        task_id: taskId,
        completed: completed
      });

      if (response.data.success) {
        // Update local state
        setCarePlan(prev => ({
          ...prev,
          daily_tasks: prev.daily_tasks.map(task => 
            task.id === taskId ? { ...task, completed } : task
          ),
          progress_tracking: {
            ...prev.progress_tracking,
            completed_tasks: prev.daily_tasks.filter(t => 
              t.id === taskId ? completed : t.completed
            ).length,
            completion_percentage: Math.round(
              (prev.daily_tasks.filter(t => 
                t.id === taskId ? completed : t.completed
              ).length / prev.daily_tasks.length) * 100
            )
          }
        }));
      }
    } catch (error) {
      console.error('Error updating task:', error);
    }
  };

  const regenerateWeeklyPlan = async () => {
    try {
      setLoading(true);
      const response = await api.post('/care-plan/regenerate', {
        user_id: currentUser.uid
      });

      if (response.data.success) {
        setCarePlan(response.data.care_plan);
        setSuccess('Your care plan has been updated for the new week!');
      }
    } catch (error) {
      setError('Error regenerating care plan');
    } finally {
      setLoading(false);
    }
  };


  const renderAssessmentStep = () => (
    <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
      <Typography variant="h5" gutterBottom>
        Care Plan Assessment
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Please provide information about your postpartum journey to generate a personalized care plan.
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <TextField
            fullWidth
            label="Delivery Date"
            type="date"
            value={formData.delivery_date}
            onChange={(e) => handleDeliveryDateChange(e.target.value)}
            InputLabelProps={{ shrink: true }}
            required
          />
        </Grid>

        <Grid item xs={12} md={6}>
          <TextField
            fullWidth
            label="Postpartum Week"
            type="number"
            value={formData.postpartum_week}
            onChange={(e) => handleInputChange('postpartum_week', parseInt(e.target.value))}
            InputProps={{ readOnly: true }}
            helperText="Automatically calculated from delivery date"
          />
        </Grid>

        <Grid item xs={12} md={6}>
          <FormControl fullWidth required>
            <InputLabel>Delivery Type</InputLabel>
            <Select
              value={formData.delivery_type}
              onChange={(e) => handleInputChange('delivery_type', e.target.value)}
              label="Delivery Type"
            >
              {deliveryTypes.map(type => (
                <MenuItem key={type.value} value={type.value}>
                  {type.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>

        <Grid item xs={12} md={6}>
          <FormControl fullWidth required>
            <InputLabel>Feeding Method</InputLabel>
            <Select
              value={formData.feeding}
              onChange={(e) => handleInputChange('feeding', e.target.value)}
              label="Feeding Method"
            >
              {feedingTypes.map(type => (
                <MenuItem key={type.value} value={type.value}>
                  {type.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>

        <Grid item xs={12}>
          <FormControl fullWidth required>
            <InputLabel>Primary Concern</InputLabel>
            <Select
              value={formData.specific_concerns}
              onChange={(e) => handleInputChange('specific_concerns', e.target.value)}
              label="Primary Concern"
            >
              {commonConcerns.map(concern => (
                <MenuItem key={concern} value={concern}>
                  {concern}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>

        <Grid item xs={12}>
          <Card variant="outlined">
            <CardContent>
              <Typography variant="h6" gutterBottom>
                PPD Assessment Score
              </Typography>
              {loadingPPD ? (
                <Box display="flex" alignItems="center" gap={2}>
                  <CircularProgress size={20} />
                  <Typography>Loading your recent PPD score...</Typography>
                </Box>
              ) : existingPPDScore !== null ? (
                <Box>
                  <Alert severity="success" sx={{ mb: 2 }}>
                    Found your recent PPD assessment score: {existingPPDScore}
                  </Alert>
                  <Typography variant="body2" color="text.secondary">
                    This score will be used for your care plan generation.
                  </Typography>
                </Box>
              ) : (
                <Box>
                  <Alert severity="warning" sx={{ mb: 2 }}>
                    No recent PPD assessment found. Please take the PPD test for accurate care plan generation.
                  </Alert>
                  <Box display="flex" gap={2} alignItems="center">
                    <Button
                      variant="contained"
                      color="primary"
                      onClick={takePPDTest}
                      startIcon={<Psychology />}
                    >
                      Take PPD Test
                    </Button>
                    <Typography variant="body2" color="text.secondary">
                      or
                    </Typography>
                    <TextField
                      label="Manual EPDS Score (0-27)"
                      type="number"
                      size="small"
                      value={formData.epds_score || ''}
                      onChange={(e) => handleInputChange('epds_score', parseInt(e.target.value))}
                      inputProps={{ min: 0, max: 27 }}
                    />
                  </Box>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Paper>
  );

  const renderGeneratingStep = () => (
    <Paper elevation={2} sx={{ p: 4, textAlign: 'center' }}>
      <CircularProgress size={60} sx={{ mb: 3 }} />
      <Typography variant="h5" gutterBottom>
        Generating Your Personalized Care Plan
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
        Our ML model is analyzing your profile and matching you with similar postpartum experiences...
      </Typography>
      <LinearProgress sx={{ width: '100%', maxWidth: 400, mx: 'auto' }} />
    </Paper>
  );

  const renderCarePlanStep = () => {
    // Calculate progress metrics
    const totalTasks = carePlan?.daily_tasks?.length || 0;
    const completedTasks = carePlan?.daily_tasks?.filter(task => task.completed)?.length || 0;
    const progressPercentage = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0;

    return (
      <Box>
        {/* Header */}
        <Paper elevation={2} sx={{ p: 3, mb: 3, background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white' }}>
          <Box sx={{ 
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', 
            color: 'white', 
            p: 4, 
            borderRadius: 3, 
            mb: 3,
            position: 'relative',
            overflow: 'hidden'
          }}>
            <Box sx={{ position: 'relative', zIndex: 2 }}>
              <Typography variant="h3" gutterBottom sx={{ fontWeight: 'bold' }}>
                🌸 Week {carePlan.postpartum_week} of Your Recovery Journey
              </Typography>
              <Typography variant="h6" sx={{ opacity: 0.9, mb: 1 }}>
                {carePlan.cluster_info?.name} | Personalized recommendations based on similar postpartum experiences
              </Typography>
              <Typography variant="body1" sx={{ opacity: 0.8 }}>
                {carePlan.cluster_info?.description}
              </Typography>
            </Box>
            <IconButton 
              onClick={regenerateWeeklyPlan}
              sx={{ 
                position: 'absolute',
                top: 16,
                right: 16,
                color: 'white', 
                bgcolor: 'rgba(255,255,255,0.2)',
                '&:hover': { bgcolor: 'rgba(255,255,255,0.3)' }
              }}
              disabled={loading}
            >
              <Refresh />
            </IconButton>
            <Box sx={{
              position: 'absolute',
              top: -50,
              right: -50,
              width: 200,
              height: 200,
              borderRadius: '50%',
              bgcolor: 'rgba(255,255,255,0.1)',
              zIndex: 1
            }} />
          </Box>
        </Paper>

        {/* Weekly Progress */}
        <Card sx={{ mb: 3, background: 'linear-gradient(45deg, #f8f9fa 0%, #e9ecef 100%)' }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <Typography variant="h5" sx={{ flexGrow: 1, fontWeight: 'bold', color: '#495057' }}>
                📊 Weekly Progress
              </Typography>
              <Chip 
                label={`${progressPercentage}% Complete`}
                color={progressPercentage >= 70 ? 'success' : progressPercentage >= 40 ? 'warning' : 'default'}
                sx={{ fontWeight: 'bold' }}
              />
            </Box>
            <Box sx={{ mb: 2 }}>
              <LinearProgress 
                variant="determinate" 
                value={progressPercentage} 
                sx={{ 
                  height: 12, 
                  borderRadius: 6,
                  bgcolor: '#e9ecef',
                  '& .MuiLinearProgress-bar': {
                    borderRadius: 6,
                    background: progressPercentage >= 70 ? 'linear-gradient(45deg, #28a745, #20c997)' : 
                               progressPercentage >= 40 ? 'linear-gradient(45deg, #ffc107, #fd7e14)' : 
                               'linear-gradient(45deg, #6c757d, #adb5bd)'
                  }
                }}
              />
            </Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Typography variant="body1" sx={{ fontWeight: 'medium' }}>
                {completedTasks} of {totalTasks} tasks completed
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {progressPercentage >= 70 ? '🎉 Great progress!' : 
                 progressPercentage >= 40 ? '💪 Keep going!' : 
                 '🌱 Every step counts!'}
              </Typography>
            </Box>
          </CardContent>
        </Card>

        {/* This Week's Priorities */}
        <Card sx={{ mb: 3, boxShadow: '0 4px 20px rgba(0,0,0,0.1)' }}>
          <CardContent sx={{ p: 4 }}>
            <Typography variant="h5" gutterBottom sx={{ fontWeight: 'bold', mb: 3, color: '#2c3e50' }}>
              🎯 This Week's Priorities
            </Typography>
            <Grid container spacing={3}>
              {carePlan.weekly_priorities?.map((priority, index) => (
                <Grid item xs={12} sm={6} md={4} key={index}>
                  <Box sx={{ 
                    p: 3, 
                    background: `linear-gradient(135deg, ${[
                      '#ff9a9e, #fecfef',
                      '#a8edea, #fed6e3', 
                      '#ffecd2, #fcb69f',
                      '#ff8a80, #ffab91',
                      '#b39ddb, #9fa8da'
                    ][index % 5]})`,
                    borderRadius: 3,
                    textAlign: 'center',
                    transform: 'translateY(0)',
                    transition: 'all 0.3s ease',
                    cursor: 'pointer',
                    '&:hover': {
                      transform: 'translateY(-5px)',
                      boxShadow: '0 8px 25px rgba(0,0,0,0.15)'
                    }
                  }}>
                    <Typography variant="h4" sx={{ mb: 1 }}>
                      {priority.icon}
                    </Typography>
                    <Typography variant="h6" gutterBottom sx={{ fontWeight: 'bold', color: '#2c3e50' }}>
                      {priority.title}
                    </Typography>
                    <Typography variant="body2" sx={{ color: '#495057', lineHeight: 1.6 }}>
                      {priority.description}
                    </Typography>
                  </Box>
                </Grid>
              ))}
            </Grid>
          </CardContent>
        </Card>

        {/* Daily Tasks */}
        <Card sx={{ boxShadow: '0 4px 20px rgba(0,0,0,0.1)' }}>
          <CardContent sx={{ p: 4 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
              <Typography variant="h5" sx={{ flexGrow: 1, fontWeight: 'bold', color: '#2c3e50' }}>
                ✅ Your Daily Tasks
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Complete tasks to build healthy habits
              </Typography>
            </Box>
            <List sx={{ p: 0 }}>
              {carePlan.daily_tasks?.map((task, index) => (
                <ListItem 
                  key={index} 
                  sx={{ 
                    mb: 2, 
                    p: 3,
                    bgcolor: task.completed ? '#f8f9fa' : '#ffffff',
                    border: '1px solid',
                    borderColor: task.completed ? '#28a745' : '#e9ecef',
                    borderRadius: 2,
                    transition: 'all 0.3s ease',
                    '&:hover': {
                      bgcolor: task.completed ? '#f8f9fa' : '#f8f9fa',
                      borderColor: task.completed ? '#28a745' : '#6c757d'
                    }
                  }}
                >
                  <ListItemIcon sx={{ minWidth: 40 }}>
                    <Checkbox
                      checked={task.completed || false}
                      onChange={(e) => handleTaskCompletion(task.id, e.target.checked)}
                      color="success"
                      sx={{
                        '& .MuiSvgIcon-root': { fontSize: 28 }
                      }}
                    />
                  </ListItemIcon>
                  <ListItemText
                    primary={
                      <Typography 
                        variant="h6" 
                        sx={{ 
                          fontWeight: 'medium',
                          textDecoration: task.completed ? 'line-through' : 'none',
                          color: task.completed ? '#6c757d' : '#2c3e50'
                        }}
                      >
                        {task.title}
                      </Typography>
                    }
                    secondary={
                      <Box sx={{ mt: 1 }}>
                        <Typography 
                          variant="body2" 
                          sx={{ 
                            color: task.completed ? '#6c757d' : '#495057',
                            mb: 1,
                            lineHeight: 1.6
                          }}
                        >
                          {task.description}
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                          <Chip 
                            label={task.category} 
                            size="small" 
                            sx={{ 
                              bgcolor: task.completed ? '#e9ecef' : '#e3f2fd',
                              color: task.completed ? '#6c757d' : '#1976d2'
                            }}
                          />
                          <Chip 
                            label={task.priority === 'high' ? '🔥 High' : task.priority === 'medium' ? '⚡ Medium' : '💙 Low'}
                            size="small"
                            color={task.priority === 'high' ? 'error' : task.priority === 'medium' ? 'warning' : 'default'}
                            variant={task.completed ? 'outlined' : 'filled'}
                          />
                          {task.completed && (
                            <Chip 
                              label="✨ Completed!"
                              size="small"
                              color="success"
                              variant="outlined"
                            />
                          )}
                        </Box>
                      </Box>
                    }
                  />
                </ListItem>
              ))}
            </List>
            {carePlan.daily_tasks?.length === 0 && (
              <Box sx={{ textAlign: 'center', py: 4 }}>
                <Typography variant="h6" color="text.secondary" gutterBottom>
                  🌟 No tasks for today!
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Take this time to rest and focus on your recovery.
                </Typography>
              </Box>
            )}
          </CardContent>
        </Card>

        {/* Resources */}
        <Card sx={{ mt: 3, boxShadow: '0 4px 20px rgba(0,0,0,0.1)' }}>
          <CardContent sx={{ p: 4 }}>
            <Typography variant="h5" gutterBottom sx={{ fontWeight: 'bold', color: '#2c3e50', mb: 3 }}>
              📚 Recommended Resources
            </Typography>
            <List sx={{ p: 0 }}>
              {carePlan?.resources?.map((resource, index) => (
                <ListItem 
                  key={index}
                  sx={{
                    mb: 1,
                    p: 2,
                    bgcolor: '#f8f9fa',
                    borderRadius: 2,
                    border: '1px solid #e9ecef',
                    '&:hover': {
                      bgcolor: '#e9ecef',
                      cursor: (typeof resource === 'object' && resource.url) ? 'pointer' : 'default'
                    }
                  }}
                >
                  <ListItemIcon>
                    <LocalHospital color="primary" />
                  </ListItemIcon>
                  <ListItemText 
                    primary={
                      (typeof resource === 'object' && resource.url) ? (
                        <a href={resource.url} target="_blank" rel="noopener noreferrer" style={{ color: 'inherit', textDecoration: 'none' }}>
                          <Typography variant="body1" sx={{ fontWeight: 'medium' }}>
                            {resource.title || resource.url}
                          </Typography>
                        </a>
                      ) : (
                        <Typography variant="body1" sx={{ fontWeight: 'medium' }}>
                          {typeof resource === 'string' ? resource : (resource.title || 'Resource')}
                        </Typography>
                      )
                    }
                    secondary={
                      (typeof resource === 'object' && resource.type) ? (
                        <Typography variant="caption" color="text.secondary">
                          {resource.type}
                        </Typography>
                      ) : null
                    }
                  />
                </ListItem>
              ))}
              {(!carePlan?.resources || carePlan.resources.length === 0) && (
                <Box sx={{ textAlign: 'center', py: 3 }}>
                  <Typography variant="body2" color="text.secondary">
                    📖 Resources will be curated based on your specific needs and recovery stage.
                  </Typography>
                </Box>
              )}
            </List>
          </CardContent>
        </Card>
      </Box>
    );
  };

  if (!currentUser) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <Typography>Please log in to access your care plan.</Typography>
      </Box>
    );
  }

  return (
    <Box className={styles.carePlanContainer} sx={{ maxWidth: 1200, mx: 'auto', p: 3 }}>
      <Typography variant="h3" gutterBottom align="center" sx={{ mb: 4 }}>
        AI-Powered Care Plan
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 3 }} onClose={() => setSuccess('')}>
          {success}
        </Alert>
      )}

      <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
        {steps.map((label) => (
          <Step key={label}>
            <StepLabel>{label}</StepLabel>
          </Step>
        ))}
      </Stepper>

      {activeStep === 0 && renderAssessmentStep()}
      {activeStep === 1 && renderGeneratingStep()}
      {activeStep === 2 && carePlan && renderCarePlanStep()}

      {activeStep < 2 && (
        <Box display="flex" justifyContent="space-between" mt={3}>
          <Button 
            disabled={activeStep === 0} 
            onClick={handleBack}
          >
            Back
          </Button>
          <Button 
            variant="contained" 
            onClick={handleNext}
            disabled={loading}
          >
            {activeStep === steps.length - 1 ? 'Finish' : 'Next'}
          </Button>
        </Box>
      )}
    </Box>
  );
};

export default CarePlan;
