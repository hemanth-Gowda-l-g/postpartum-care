import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  IconButton,
  CircularProgress,
  Alert,
  Tabs,
  Tab,
  Card,
  CardContent,
  CardHeader,
  Chip,
  Tooltip,
  LinearProgress,
} from '@mui/material';

import {
  Restaurant as RestaurantIcon,
  LocalDining as DietIcon,
  Warning as AllergyIcon,
  Bloodtype as DeficiencyIcon,
  Public as CuisineIcon,
  Psychology as AnalysisIcon,
  Psychology,
  Timeline as TimelineIcon,
  CalendarToday as CalendarIcon,
  TrendingUp as TrendingUpIcon,
  InfoOutlined as InfoOutlinedIcon,
  LocalDrink as LocalDrinkIcon,
  LightbulbOutlined as LightbulbIcon,
  Save as SaveIcon,
} from '@mui/icons-material';

import axios from 'axios';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip as ChartTooltip,
  Legend,
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  ChartTooltip,
  Legend
);

const NutritionPrediction = () => {
  const [formData, setFormData] = useState({
    breastfeeding: '',
    dietType: '',
    allergies: '',
    deficiency: [],
    preferredCuisine: '',
  });

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState(0);
  const [progressData, setProgressData] = useState({});
  const [trackingValue, setTrackingValue] = useState('');
  const [hydrationCups, setHydrationCups] = useState(() => Number(localStorage.getItem('hydration_cups') || 0));

  const handleChange = (field) => (event) => {
    const { value } = event.target || {};
    // Ensure MUI multiple Select stores an array, not a comma string
    if (field === 'deficiency') {
      const nextVal = typeof value === 'string' ? value.split(',').map(v => v.trim()).filter(Boolean) : (Array.isArray(value) ? value : []);
      setFormData({
        ...formData,
        deficiency: nextVal,
      });
      return;
    }
    setFormData({
      ...formData,
      [field]: value,
    });
  };

  const handleSaveProfile = async () => {
    try {
      const token = localStorage.getItem('token');
      // Save locally for quick reuse
      localStorage.setItem('nutrition_profile', JSON.stringify(formData));
      // Try saving to backend if available
      try {
        await axios.post('/api/nutrition/profile', formData, {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });
      } catch (apiErr) {
        // Non-fatal for UX; profile is saved locally
        console.log('Profile saved locally; backend save not available:', apiErr?.response?.status);
      }
      setError('');
    } catch (err) {
      setError('Failed to save profile.');
    }
  };

  const toggleHydrationCup = (index) => {
    let next = hydrationCups;
    if (index < hydrationCups) next = index; // unfill down to index
    else next = index + 1; // fill up to index
    setHydrationCups(next);
    localStorage.setItem('hydration_cups', String(next));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setResult(null);

    try {
      const token = localStorage.getItem('token');

      if (!token) {
        setError('Please log in to get personalized nutrition recommendations.');
        setLoading(false);
        return;
      }

      // Always use model-driven endpoint
      const response = await axios.post('/api/nutrition/predict', formData, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      setResult(response.data);
      setActiveTab(3); // jump user directly to Meal Plan tab

    } catch (err) {
      if (err.response?.status === 401) {
        setError('Please log in to get nutrition recommendations.');
      } else {
        setError('Failed to get nutrition recommendations. Please try again.');
      }
      console.error('Nutrition prediction error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  const handleTrackProgress = async (category) => {
    try {
      const token = localStorage.getItem('token');
      await axios.post('/api/nutrition/track', {
        category,
        value: trackingValue
      }, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      setTrackingValue('');
      fetchProgressData(category);
    } catch (err) {
      setError('Failed to track progress. Please try again.');
    }
  };

  const fetchProgressData = async (category) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`/api/nutrition/progress/${category}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      setProgressData(prev => ({
        ...prev,
        [category]: response.data.progress
      }));
    } catch (err) {
      console.error('Failed to fetch progress data:', err);
    }
  };

  useEffect(() => {
    if (activeTab === 1) {
      fetchProgressData('daily_calories');
    }
  }, [activeTab]);

  const renderProgressChart = (category) => {
    const data = progressData[category] || [];
    const chartData = {
      labels: data.map(d => new Date(d.date).toLocaleDateString()),
      datasets: [
        {
          label: category.replace('_', ' ').toUpperCase(),
          data: data.map(d => d.value),
          borderColor: 'rgb(75, 192, 192)',
          tension: 0.1,
        },
      ],
    };

    return (
      <Box sx={{ mt: 2 }}>
        <Line data={chartData} />
      </Box>
    );
  };

  const renderMealPlan = () => {
    // Prefer model-driven recommendations if present
    const xgb = result?.xgb_recommendations || [];
    if (xgb.length > 0) {
      const buckets = { Breakfast: [], Lunch: [], Dinner: [] };
      const order = ['Breakfast', 'Lunch', 'Dinner'];
      xgb.forEach((r, i) => {
        const label = r?.description || `Food #${i + 1}`;
        buckets[order[i % 3]].push(label);
      });
      const mealPlan = [
        { meal_type: 'Breakfast', suggestions: buckets.Breakfast },
        { meal_type: 'Lunch', suggestions: buckets.Lunch },
        { meal_type: 'Dinner', suggestions: buckets.Dinner },
      ];
      return (
        <Grid container spacing={2}>
          {mealPlan.map((meal, index) => (
            <Grid item xs={12} md={4} key={index}>
              <Card>
                <CardHeader
                  title={`${meal.meal_type} (Model-based)`}
                  avatar={<RestaurantIcon color="primary" />}
                />
                <CardContent>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Suggestions:
                  </Typography>
                  {meal.suggestions.map((suggestion, idx) => (
                    <Typography key={idx} variant="body2" sx={{ mb: 1 }}>
                      • {suggestion}
                    </Typography>
                  ))}
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      );
    }

    console.log('Meal plan data:', result?.meal_plan);
    if (!result?.meal_plan) {
      return (
        <Typography variant="body2" color="text.secondary">
          No meal plan available. Please generate recommendations first.
        </Typography>
      );
    }

    return (
      <Grid container spacing={2}>
        {result.meal_plan.map((meal, index) => (
          <Grid item xs={12} md={4} key={index}>
            <Card>
              <CardHeader
                title={meal.meal_type}
                avatar={<RestaurantIcon color="primary" />}
              />
              <CardContent>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  Suggestions:
                </Typography>
                {meal.suggestions.map((suggestion, idx) => (
                  <Typography key={idx} variant="body2" sx={{ mb: 1 }}>
                    • {suggestion}
                  </Typography>
                ))}
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    );
  };

  const renderRecommendations = () => {
    if (!result?.recommendations) return null;

    return (
      <Grid container spacing={2}>
        {result.recommendations.map((rec, index) => (
          <Grid item xs={12} key={index}>
            <Paper
              elevation={rec.knn_enhanced ? 3 : 1}
              sx={{
                p: 2,
                bgcolor: rec.knn_enhanced ? '#e3f2fd' : 'white',
                border: rec.ai_generated ? '2px solid #1976d2' : 'none'
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Typography variant="subtitle1" color="primary" sx={{ flexGrow: 1 }}>
                  {rec.title}
                </Typography>
                {rec.knn_enhanced && (
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <AnalysisIcon color="primary" fontSize="small" />
                    <Typography variant="caption" color="primary" fontWeight="bold">
                      AI Enhanced
                    </Typography>
                  </Box>
                )}
                {rec.ai_generated && (
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, ml: 1 }}>
                    <Psychology color="secondary" fontSize="small" />
                    <Typography variant="caption" color="secondary" fontWeight="bold">
                      AI Generated
                    </Typography>
                  </Box>
                )}
              </Box>
              <Typography variant="body2" sx={{ mb: 1 }}>
                {rec.description}
              </Typography>
              {rec.knn_similarity_score && (
                <Typography variant="caption" color="text.secondary">
                  Similarity Score: {rec.knn_similarity_score}
                </Typography>
              )}
              {rec.priority && (
                <Typography variant="caption" color="text.secondary" sx={{ ml: 2 }}>
                  Priority: {rec.priority}
                </Typography>
              )}
            </Paper>
          </Grid>
        ))}
      </Grid>
    );
  };

  return (
    <Container maxWidth="md">
      <Box sx={{ my: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom align="center" color="primary">
          Postpartum Nutrition Profile
        </Typography>
        <Typography variant="subtitle1" align="center" color="text.secondary" sx={{ mb: 2 }}>
          Get personalized nutrition recommendations based on your preferences
        </Typography>

        {/* Step indicator */}
        <Box sx={{ mb: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
            <Typography variant="caption" color="text.secondary">Step 1 of 3: Nutrition Profile</Typography>
            <Typography variant="caption" color="text.secondary">Complete your profile to unlock recommendations</Typography>
          </Box>
          <LinearProgress variant="determinate" value={33} />
        </Box>

        <Paper elevation={3} sx={{ p: 4, mb: 3 }}>
          <form onSubmit={handleSubmit}>
            <Grid container spacing={3}>
              <Grid xs={12} sm={6} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Are you currently breastfeeding?</InputLabel>
                  <Select
                    value={formData.breastfeeding}
                    onChange={handleChange('breastfeeding')}
                    required
                    startAdornment={
                      <IconButton size="small" sx={{ mr: 1 }}>
                        <RestaurantIcon color="primary" />
                      </IconButton>
                    }
                  >
                    <MenuItem value="yes">Yes</MenuItem>
                    <MenuItem value="no">No</MenuItem>
                  </Select>
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5 }}>
                    Helps adjust energy and nutrient needs.
                  </Typography>
                </FormControl>
              </Grid>

              <Grid xs={12} sm={6} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Diet type</InputLabel>
                  <Select
                    value={formData.dietType}
                    onChange={handleChange('dietType')}
                    required
                    startAdornment={
                      <IconButton size="small" sx={{ mr: 1 }}>
                        <DietIcon color="primary" />
                      </IconButton>
                    }
                  >
                    <MenuItem value="vegetarian">Vegetarian</MenuItem>
                    <MenuItem value="vegan">Vegan</MenuItem>
                    <MenuItem value="omnivore">Omnivore</MenuItem>
                  </Select>
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5 }}>
                    We strictly respect diet restrictions in recommendations.
                  </Typography>
                </FormControl>
              </Grid>

              <Grid xs={12} sm={6} md={6}>
                <TextField
                  fullWidth
                  label="Allergies (comma-separated)"
                  value={formData.allergies}
                  onChange={handleChange('allergies')}
                  placeholder="Enter allergies separated by commas"
                  InputProps={{
                    startAdornment: (
                      <IconButton size="small" sx={{ mr: 1 }}>
                        <AllergyIcon color="primary" />
                      </IconButton>
                    ),
                    endAdornment: (
                      <Tooltip title="This helps us avoid ingredients that may cause reactions.">
                        <IconButton size="small">
                          <InfoOutlinedIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    ),
                  }}
                />
                <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                  Example: milk, peanuts, gluten
                </Typography>
              </Grid>

              <Grid xs={12} sm={6} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Known nutrient deficiencies</InputLabel>
                  <Select
                    multiple
                    value={formData.deficiency}
                    onChange={handleChange('deficiency')}
                    startAdornment={
                      <IconButton size="small" sx={{ mr: 1 }}>
                        <DeficiencyIcon color="primary" />
                      </IconButton>
                    }
                  >
                    <MenuItem value={"iron"}>Iron</MenuItem>
                    <MenuItem value={"b12"}>B12</MenuItem>
                    <MenuItem value={"calcium"}>Calcium</MenuItem>
                    <MenuItem value={"vitamin_d"}>Vitamin D</MenuItem>
                    <MenuItem value={"folate"}>Folate</MenuItem>
                    <MenuItem value={"zinc"}>Zinc</MenuItem>
                  </Select>
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5 }}>
                    Select one or more nutrients to prioritize.
                  </Typography>
                </FormControl>
              </Grid>

              <Grid xs={12} sm={6} md={6}>
                <TextField
                  fullWidth
                  label="Preferred cuisine"
                  value={formData.preferredCuisine}
                  onChange={handleChange('preferredCuisine')}
                  placeholder="e.g., Indian, Mediterranean"
                  required
                  InputProps={{
                    startAdornment: (
                      <IconButton size="small" sx={{ mr: 1 }}>
                        <CuisineIcon color="primary" />
                      </IconButton>
                    ),
                    endAdornment: (
                      <Tooltip title="Pick a cuisine you enjoy to tailor your plan.">
                        <IconButton size="small">
                          <InfoOutlinedIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    ),
                  }}
                />
                <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                  We boost foods matching your preferred cuisine when possible.
                </Typography>
              </Grid>

              <Grid xs={12}>
                <Button
                  type="submit"
                  variant="contained"
                  color="primary"
                  size="large"
                  fullWidth
                  disabled={loading}
                  startIcon={loading ? <CircularProgress size={20} /> : <AnalysisIcon />}
                >
                  {loading ? 'Analyzing...' : 'Get Recommendations'}
                </Button>
              </Grid>
              <Grid xs={12}>
                <Button
                  type="button"
                  variant="outlined"
                  color="primary"
                  size="large"
                  fullWidth
                  onClick={handleSaveProfile}
                  startIcon={<SaveIcon />}
                >
                  Save Profile
                </Button>
              </Grid>
            </Grid>
          </form>
        </Paper>

        {/* Profile summary */}
        <Paper elevation={1} sx={{ p: 2, mb: 3 }}>
          <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1 }}>Your selections</Typography>
          <Typography variant="body2" color="text.secondary">
            You are {formData.breastfeeding === 'yes' ? 'breastfeeding' : 'not breastfeeding'}, prefer a {formData.dietType || '—'} diet,
            enjoy {formData.preferredCuisine || '—'} cuisine, and reported {formData.allergies || 'no'} allergies.
            {Array.isArray(formData.deficiency) && formData.deficiency.length > 0 ? ` We will prioritize ${formData.deficiency.map(d => String(d).toUpperCase()).join(', ')}-rich foods.` : ''}
          </Typography>
        </Paper>

        {/* Health context cards (horizontal slider) */}
        <Box
          sx={{
            mb: 4,
            display: 'flex',
            gap: 2,
            overflowX: 'auto',
            pb: 1,
            scrollSnapType: 'x mandatory',
            WebkitOverflowScrolling: 'touch',
            '&::-webkit-scrollbar': { display: 'none' },
            msOverflowStyle: 'none',
            scrollbarWidth: 'none',
          }}
        >
          <Card sx={{ flex: '0 0 auto', minWidth: 300, scrollSnapAlign: 'start' }}>
            <CardHeader avatar={<DeficiencyIcon color="error" />} title="Nutrient Focus" />
            <CardContent>
              <Typography variant="body2">Iron, Calcium, Protein are key postpartum. {Array.isArray(formData.deficiency) && formData.deficiency.includes('iron') && 'We will emphasize iron-rich foods.'} {Array.isArray(formData.deficiency) && formData.deficiency.includes('b12') && 'We will emphasize B12-rich foods.'} {Array.isArray(formData.deficiency) && formData.deficiency.includes('calcium') && 'We will emphasize calcium-rich foods.'}</Typography>
            </CardContent>
          </Card>
          <Card sx={{ flex: '0 0 auto', minWidth: 300, scrollSnapAlign: 'start' }}>
            <CardHeader avatar={<TrendingUpIcon color="primary" />} title="Energy Needs" />
            <CardContent>
              <Typography variant="body2">Typical needs: +300–500 kcal/day when breastfeeding. Listen to hunger and fullness.</Typography>
            </CardContent>
          </Card>
          <Card sx={{ flex: '0 0 auto', minWidth: 300, scrollSnapAlign: 'start' }}>
            <CardHeader avatar={<LocalDrinkIcon color="info" />} title="Hydration" />
            <CardContent>
              <Typography variant="body2">Target ~2–3 liters water/day. Use the cups tracker below.</Typography>
            </CardContent>
          </Card>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {error}
          </Alert>
        )}

        {result && (
          <Box sx={{ mt: 4 }}>
            {/* Sentiment-aware banner (shown after recommendations fetched) */}
            {result?.ai_insights?.sentiment && (
              <Paper elevation={0} sx={{
                mb: 2,
                p: 2,
                borderRadius: 2,
                background: '#F3F4FF',
                border: '1px solid #E0E7FF'
              }}>
                <Typography variant="body2" sx={{ color: '#3730A3', fontWeight: 600 }}>
                  Sentiment-aware (DNN): {result.ai_insights.sentiment.adjustment?.mode || 'neutral'} · 7-day avg: {result.ai_insights.sentiment.last7_avg != null ? Number(result.ai_insights.sentiment.last7_avg).toFixed(2) : 'N/A'}
                </Typography>
                {(result.ai_insights.sentiment.latest_mood != null || result.ai_insights.sentiment.current != null) && (
                  <Typography variant="caption" sx={{ color: '#4338CA', display: 'block' }}>
                    Latest mood: {result.ai_insights.sentiment.latest_mood ?? '—'} · Current sentiment: {result.ai_insights.sentiment.current != null ? Number(result.ai_insights.sentiment.current).toFixed(2) : 'N/A'}
                  </Typography>
                )}
                <Typography variant="caption" sx={{ color: '#4B5563' }}>
                  Source: {result.ai_insights.sentiment.source || '—'}. Your recent mood trend influences how foods are ranked to support adherence and postpartum nutrition needs.
                </Typography>
              </Paper>
            )}
            <Tabs value={activeTab} onChange={handleTabChange} centered>
              <Tab icon={<RestaurantIcon />} label="Recommendations" />
              <Tab icon={<AnalysisIcon />} label="AI Insights" />
              <Tab icon={<TimelineIcon />} label="Progress Tracking" />
              <Tab icon={<CalendarIcon />} label="Meal Plan" />
            </Tabs>

            <Box sx={{ mt: 3 }}>
              {activeTab === 0 && (
                <Paper elevation={3} sx={{ p: 3, bgcolor: '#f8f9fa' }}>
                  <Typography variant="h6" gutterBottom color="primary">
                    Your Personalized Nutrition Recommendations
                  </Typography>
                  {result?.fallback_mode && (
                    <Alert severity="info" sx={{ mb: 2 }}>
                      {result.message || 'Using basic recommendations'}
                    </Alert>
                  )}
                  {!result?.fallback_mode && result?.knn_insights && (
                    <Alert severity="success" sx={{ mb: 2 }}>
                      Enhanced with AI-powered K-NN analysis
                    </Alert>
                  )}
                  {renderRecommendations()}
                </Paper>
              )}

              {activeTab === 1 && (
                <Paper elevation={3} sx={{ p: 3, bgcolor: '#f8f9fa' }}>
                  <Typography variant="h6" gutterBottom color="primary">
                    AI-Powered Insights
                  </Typography>
                  {result?.ai_insights ? (
                    <Grid container spacing={3}>
                      <Grid item xs={12} md={6}>
                        <Card>
                          <CardHeader title="RDA Coverage (Top Foods)" />
                          <CardContent>
                            {Array.isArray(result.ai_insights.rda_coverage) && result.ai_insights.rda_coverage.length > 0 ? (
                              result.ai_insights.rda_coverage.map((row, idx) => (
                                <Typography key={idx} variant="body2" gutterBottom>
                                  {row.nutrient}: {row.avg_pct}% of RDA (avg)
                                </Typography>
                              ))
                            ) : (
                              <Typography variant="body2" color="text.secondary">No RDA stats available.</Typography>
                            )}
                          </CardContent>
                        </Card>
                      </Grid>

                      <Grid item xs={12} md={6}>
                        <Card>
                          <CardHeader title="Deficiency Focus" />
                          <CardContent>
                            {(() => {
                              const df = result?.ai_insights?.deficiency_focus;
                              const items = Array.isArray(df) ? df : (df ? [df] : []);
                              if (items.length === 0) {
                                return <Typography variant="body2" color="text.secondary">No deficiency selected.</Typography>;
                              }
                              return (
                                <Box>
                                  <Box sx={{ mb: 1 }}>
                                    <Typography variant="body2" gutterBottom>
                                      Targets: {items.map(x => String(x.target || '').toUpperCase()).join(', ')}
                                    </Typography>
                                  </Box>
                                  {items.map((it, idx) => (
                                    <Box key={idx} sx={{ mb: 1.5 }}>
                                      <Typography variant="subtitle2" color="text.secondary">
                                        {String(it.target || '').toUpperCase()} ({it.nutrient_key || '—'})
                                      </Typography>
                                      {Array.isArray(it.top_foods) && it.top_foods.length > 0 ? (
                                        it.top_foods.map((f, i) => (
                                          <Typography key={i} variant="body2" gutterBottom>
                                            • {f.description}: {f.amount}{f.unit} ({f.rda_pct}% RDA)
                                          </Typography>
                                        ))
                                      ) : (
                                        <Typography variant="body2" color="text.secondary">No specific foods highlighted.</Typography>
                                      )}
                                    </Box>
                                  ))}
                                </Box>
                              );
                            })()}
                          </CardContent>
                        </Card>
                      </Grid>

                      

                      <Grid item xs={12} md={6}>
                        <Card>
                          <CardHeader title="Filter Impact & Diversity" />
                          <CardContent>
                            <Typography variant="body2">Candidates after filters: {result.ai_insights.filter_impact?.candidates_after_filters ?? '—'}</Typography>
                            {result.ai_insights.filter_impact?.cuisine_matches !== null && result.ai_insights.filter_impact?.cuisine_matches !== undefined && (
                              <Typography variant="body2">Cuisine matches (boosted): {result.ai_insights.filter_impact.cuisine_matches}</Typography>
                            )}
                            <Typography variant="body2" sx={{ mt: 1 }}>Unique categories: {result.ai_insights.diversity?.unique_categories ?? '—'}</Typography>
                          </CardContent>
                        </Card>
                      </Grid>

                      {/* Optional: Sodium caution derived from RDA coverage */}
                      {Array.isArray(result.ai_insights.rda_coverage) && result.ai_insights.rda_coverage.some(x => (x.nutrient || '').toLowerCase().includes('sodium') && Number(x.avg_pct) > 100) && (
                        <Grid item xs={12}>
                          <Alert severity="warning">
                            Sodium intake appears high across the top foods. Consider balancing with fresh produce and hydration.
                          </Alert>
                        </Grid>
                      )}
                    </Grid>
                  ) : (
                    <Alert severity="info">Insights will appear after generating recommendations.</Alert>
                  )}
                </Paper>
              )}

              {activeTab === 2 && (
                <Paper elevation={3} sx={{ p: 3, bgcolor: '#f8f9fa' }}>
                  <Typography variant="h6" gutterBottom color="primary">
                    Track Your Progress
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={12} md={6}>
                      <TextField
                        fullWidth
                        label="Enter Value"
                        value={trackingValue}
                        onChange={(e) => setTrackingValue(e.target.value)}
                        type="number"
                      />
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <Button
                        variant="contained"
                        color="primary"
                        onClick={() => handleTrackProgress('daily_calories')}
                        startIcon={<TrendingUpIcon />}
                      >
                        Track Calories
                      </Button>
                    </Grid>
                  </Grid>
                  {renderProgressChart('daily_calories')}
                </Paper>
              )}

              {activeTab === 3 && (
                <Paper elevation={3} sx={{ p: 3, bgcolor: '#f8f9fa' }}>
                  <Typography variant="h6" gutterBottom color="primary">
                    Your Personalized Meal Plan
                  </Typography>
                  {renderMealPlan()}
                </Paper>
              )}
            </Box>
          </Box>
        )}

        {/* Engagement: Tips and Hydration tracker */}
        <Grid container spacing={2} sx={{ mt: 2 }}>
          <Grid item xs={12} md={8}>
            <Paper elevation={2} sx={{ p: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <LightbulbIcon color="warning" />
                <Typography variant="subtitle1">Daily Tip</Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Soaking almonds or sesame can improve mineral absorption. Pair vitamin C with iron-rich foods.
              </Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} md={4}>
            <Paper elevation={2} sx={{ p: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <LocalDrinkIcon color="info" />
                <Typography variant="subtitle1">Hydration</Typography>
              </Box>
              <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                {Array.from({ length: 8 }).map((_, i) => (
                  <Chip
                    key={i}
                    label={i < hydrationCups ? '💧' : '○'}
                    color={i < hydrationCups ? 'primary' : 'default'}
                    onClick={() => toggleHydrationCup(i)}
                    size="small"
                  />
                ))}
              </Box>
            </Paper>
          </Grid>
        </Grid>
      </Box>
    </Container>
  );
};

export default NutritionPrediction;