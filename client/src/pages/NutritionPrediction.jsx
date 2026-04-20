import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import styles from '../styles/NutritionPrediction.module.scss';
import api from '../services/api';
import { Box, Typography, Paper, CircularProgress, List, ListItem, ListItemText } from '@mui/material';

const NutritionPrediction = () => {
  const { currentUser } = useAuth();
  const [loadingRecommendations, setLoadingRecommendations] = useState(false);
  const [recommendedFoods, setRecommendedFoods] = useState(null);
  const [recommendationError, setRecommendationError] = useState(null);
  const [mealPlan, setMealPlan] = useState(null);
  const [recommendationStatus, setRecommendationStatus] = useState(null);
  const [aiInsights, setAiInsights] = useState(null);

  const [userNutritionProfile, setUserNutritionProfile] = useState(null);
  const [loadingProfile, setLoadingProfile] = useState(true);
  const [profileError, setProfileError] = useState(null);

  useEffect(() => {
    const fetchProfile = async () => {
      if (!currentUser) {
        setLoadingProfile(false);
        return;
      }
      try {
        const token = localStorage.getItem('token');
        const response = await api.get('/nutrition/profile', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        if (response.data) {
          setUserNutritionProfile(response.data);
        } else {
          setUserNutritionProfile({});
          console.warn("Nutrition profile not found for user. Recommendations will use default values.");
        }
      } catch (err) {
        console.error('Error fetching nutrition profile:', err);
        setProfileError('Failed to load nutrition profile.');
      } finally {
        setLoadingProfile(false);
      }
    };
    fetchProfile();
  }, [currentUser]);

  const handleGetRecommendations = async () => {
    if (!userNutritionProfile) {
      console.warn("User profile not loaded yet.");
      return;
    }
    setLoadingRecommendations(true);
    setRecommendationError(null);
    setRecommendedFoods(null);
    setMealPlan(null);
    setRecommendationStatus(null);

    try {
      const token = localStorage.getItem('token');
      const response = await api.post('/nutrition/predict', userNutritionProfile, {
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.data) {
        // Prefer model-driven list if present
        const modelRecs = response.data.xgb_recommendations || response.data.recommended_foods || [];
        setRecommendedFoods(modelRecs);
        setMealPlan(response.data.meal_plan);
        setRecommendationStatus(response.data.recommendation_status || 'Success');
        setAiInsights(response.data.ai_insights || null);
      } else {
        setRecommendationError('Received empty response data.');
      }

    } catch (err) {
      console.error('Error fetching nutrition recommendations:', err);
      setRecommendationError(err.response?.data?.error || 'Failed to get nutrition recommendations');
    } finally {
      setLoadingRecommendations(false);
    }
  };

  if (!currentUser) {
    return <Typography variant="h6">Please log in to access nutrition recommendations.</Typography>;
  }

  return (
    <div className={styles.container}>
      <Typography variant="h4" component="h1" gutterBottom>Personalized Nutrition Recommendations</Typography>

      {loadingProfile && <Box sx={{ display: 'flex', justifyContent: 'center' }}><CircularProgress /></Box>}
      {profileError && <Typography color="error">{profileError}</Typography>}

      {/* Sentiment-aware banner (shows after recommendations fetched) */}
      {aiInsights?.sentiment && (
        <Paper elevation={0} sx={{
          mt: 2,
          p: 2,
          borderRadius: 2,
          background: '#F3F4FF',
          border: '1px solid #E0E7FF'
        }}>
          <Typography variant="body2" sx={{ color: '#3730A3', fontWeight: 600 }}>
            Sentiment-aware: {aiInsights.sentiment.adjustment?.mode || 'neutral'} (7-day avg: {aiInsights.sentiment.last7_avg != null ? aiInsights.sentiment.last7_avg.toFixed(2) : 'N/A'})
          </Typography>
          <Typography variant="caption" sx={{ color: '#4B5563' }}>
            Your recent mood trend influences how foods are ranked to support adherence and postpartum nutrition needs.
          </Typography>
        </Paper>
      )}

      {userNutritionProfile && !profileError && (
        <Box sx={{ mt: 3 }}>
          <Typography variant="h6" gutterBottom>Get Your Recommendations</Typography>
          <button
            onClick={handleGetRecommendations}
            disabled={loadingRecommendations}
            className={styles.predictButton}
          >
            {loadingRecommendations ? 'Generating Recommendations...' : 'Get My Recommendations'}
          </button>
        </Box>
      )}

      {recommendationError && (
        <Typography color="error" sx={{ mt: 2 }}>
          {recommendationError}
        </Typography>
      )}

      {recommendationStatus && recommendationStatus !== "Success" && !recommendationError && (
        <Typography color="warning" sx={{ mt: 2 }}>
          Status: {recommendationStatus}
        </Typography>
      )}

      {recommendedFoods && recommendedFoods.length > 0 && (
        <Box sx={{ mt: 3 }}>
          <Typography variant="h5" gutterBottom>Recommended Foods</Typography>
          <List>
            {recommendedFoods.map((food, index) => (
              <Paper key={index} elevation={1} sx={{ mb: 2, p: 2 }}>
                <Typography variant="h6">{food.description || food.food_name}</Typography>
                {Array.isArray(food.nutrients) && food.nutrients.length > 0 && (
                  <>
                    <Typography variant="body2" sx={{ mt: 1, fontWeight: 'bold' }}>Nutrient Details:</Typography>
                    <List dense={true}>
                      {food.nutrients.slice(0, 6).map((n, nutrientIndex) => (
                        <ListItem key={nutrientIndex} disablePadding>
                          <ListItemText
                            primary={`${n.name}: ${n.amount} ${n.unit} (${n.rda_pct}% RDA)`}
                            primaryTypographyProps={{ variant: 'body2' }}
                          />
                        </ListItem>
                      ))}
                    </List>
                  </>
                )}
              </Paper>
            ))}
          </List>
        </Box>
      )}

      {/* Optionally display mealPlan here if desired */}
      {/* {mealPlan && mealPlan.length > 0 && ( */}
      {/*    <Box sx={{ mt: 3 }}> */}
      {/*        <Typography variant="h5" gutterBottom>Suggested Meal Plan</Typography> */}
      {/*        {mealPlan.map((meal, index) => ( */}
      {/*            <Box key={index} sx={{ mb: 2 }}> */}
      {/*                <Typography variant="h6">{meal.meal_type}</Typography> */}
      {/*                <List dense={true}> */}
      {/*                    {meal.suggestions.map((suggestion, sIndex) => ( */}
      {/*                        <ListItem key={sIndex} disablePadding> */}
      {/*                             <ListItemText primary={suggestion} /> */}
      {/*                        </ListItem> */}
      {/*                    ))} */}
      {/*                </List> */}
      {/*            </Box> */}
      {/*        ))} */}
      {/*    </Box> */}
      {/* )} */}
    </div>
  );
};

export default NutritionPrediction; 