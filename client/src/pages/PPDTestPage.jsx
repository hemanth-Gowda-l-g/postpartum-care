import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import { useNavigate } from 'react-router-dom';
import styles from '../styles/PPDTestPage.module.scss';
import { CircularProgress, Box, Typography, Paper, Button, Avatar, List, ListItem, ListItemText, IconButton } from '@mui/material'; // Import Material UI components
import {
    Psychology as PsychologyIcon,
    Info as InfoIcon,
    Help as HelpIcon,
    Warning as WarningIcon,
    ChevronLeft as ChevronLeftIcon,
    ChevronRight as ChevronRightIcon
} from '@mui/icons-material';

// Define the questions (ensure these match your backend's expected features)
const questions = {
    'Age': { text: 'Your Age', type: 'number' },
    'Feeling sad or Tearful': { text: 'Have you felt sad or tearful?', type: 'select', options: ['No', 'Sometimes', 'Yes'] },
    'Irritable towards baby & partner': { text: 'Have you felt irritable towards your baby or partner?', type: 'select', options: ['No', 'Sometimes', 'Yes'] },
    'Trouble sleeping at night': { text: 'How often have you had trouble sleeping at night?', type: 'select', options: ['No', 'Yes', 'Two or more days a week'] },
    'Problems concentrating or making decision': { text: 'Have you had problems concentrating or making decisions?', type: 'select', options: ['No', 'Yes', 'Often'] },
    'Overeating or loss of appetite': { text: 'Have you had changes in appetite (overeating or loss of appetite)?', type: 'select', options: ['No', 'Yes', 'Not at all'] },
    'Feeling anxious': { text: 'Have you been feeling anxious?', type: 'select', options: ['No', 'Yes'] },
    'Feeling of guilt': { text: 'Have you had feelings of guilt?', type: 'select', options: ['No', 'Maybe', 'Yes'] },
    'Problems of bonding with baby': { text: 'Have you had problems bonding with your baby?', type: 'select', options: ['No', 'Sometimes', 'Yes'] },
};

const PPDTestPage = () => {
    const [answers, setAnswers] = useState({});
    const [prediction, setPrediction] = useState(null);
    const [probability, setProbability] = useState(null); // State to store probability
    const [assistance, setAssistance] = useState(null); // State to store assistance
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [freeText, setFreeText] = useState(''); // Optional free-text notes
    const { currentUser } = useAuth();
    const navigate = useNavigate();
    const resultsRef = useRef(null); // Ref for scrolling
    const infoScrollRef = useRef(null); // Ref for horizontal scroll of info tiles

    // Redirect if not logged in (although PrivateRoute handles this, good to have here too)
    useEffect(() => {
        if (!currentUser) {
            navigate('/login');
        }
    }, [currentUser, navigate]);

    const handleInputChange = (questionKey, value) => {
        setAnswers(prev => ({
            ...prev,
            [questionKey]: value
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        setPrediction(null);
        setProbability(null); // Clear previous results
        setAssistance(null);

        // Basic validation: check if all questions are answered
        const allAnswered = Object.keys(questions).every(key => answers[key] !== undefined && answers[key] !== '');
        if (!allAnswered) {
            setError('Please answer all questions.');
            setLoading(false);
            return;
        }

        try {
            const token = localStorage.getItem('token');
            const payload = { ...answers };
            if (freeText && freeText.trim()) {
                payload.free_text = freeText.trim();
            }
            const response = await api.post('/ml/analyze-ppd', payload, {
                headers: {
                    Authorization: `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });
            setPrediction(response.data.prediction);
            setProbability(response.data.probability); // Store probability
            setAssistance(response.data.assistance); // Store assistance
            
            // Scroll to results after state update
            // Use a small timeout to ensure DOM update before scrolling
            setTimeout(() => {
                resultsRef.current?.scrollIntoView({ behavior: 'smooth' });
            }, 100);

        } catch (err) {
            console.error('PPD Analysis Error:', err);
            setError(err.response?.data?.msg || 'Failed to analyze PPD risk.');
        } finally {
            setLoading(false);
        }
    };

    // Function to navigate to Mental Health page
    const handleGoToMentalHealth = () => {
        navigate('/mental-health');
    };

    // Render the component
    return (
        <div className={styles.container}>
            <Typography variant="h4" component="h2" gutterBottom className={styles.heading}>
                Postpartum Depression Risk Analyzer
            </Typography>
            <div className={styles.subtitle}>
                Answer a few questions to assess your risk and get support resources.
            </div>
            {/* Educational cards about postpartum mental health — horizontal scrollable tiles */}
            <Box sx={{ mt: 2, mb: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 1 }}>
                    <IconButton size="small" aria-label="scroll left" onClick={() => infoScrollRef.current?.scrollBy({ left: -320, behavior: 'smooth' })}>
                        <ChevronLeftIcon />
                    </IconButton>
                    <IconButton size="small" aria-label="scroll right" onClick={() => infoScrollRef.current?.scrollBy({ left: 320, behavior: 'smooth' })}>
                        <ChevronRightIcon />
                    </IconButton>
                </Box>
                <Box ref={infoScrollRef} sx={{ display: 'flex', gap: 2, overflowX: 'auto', pb: 1, scrollBehavior: 'smooth' }}>
                    {/* Card 1 */}
                    <Paper elevation={1} sx={{ p: 2, borderRadius: 3, minWidth: 260, '&:hover': { boxShadow: 3 } }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                            <Avatar sx={{ bgcolor: 'rgba(147,197,253,0.35)', color: '#1e40af' }}>
                                <InfoIcon />
                            </Avatar>
                            <Box>
                                <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>What is PPD?</Typography>
                                <Typography variant="caption" color="text.secondary">Common, treatable mood condition after childbirth.</Typography>
                            </Box>
                        </Box>
                    </Paper>
                    {/* Card 2 */}
                    <Paper elevation={1} sx={{ p: 2, borderRadius: 3, minWidth: 260, '&:hover': { boxShadow: 3 } }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                            <Avatar sx={{ bgcolor: 'rgba(134,239,172,0.45)', color: '#166534' }}>
                                <PsychologyIcon />
                            </Avatar>
                            <Box>
                                <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>Common signs</Typography>
                                <Typography variant="caption" color="text.secondary">Sadness, anxiety, sleep/appetite changes, bonding issues.</Typography>
                            </Box>
                        </Box>
                    </Paper>
                    {/* Card 3 */}
                    <Paper elevation={1} sx={{ p: 2, borderRadius: 3, minWidth: 260, '&:hover': { boxShadow: 3 } }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                            <Avatar sx={{ bgcolor: 'rgba(255,237,213,0.8)', color: '#92400e' }}>
                                <HelpIcon />
                            </Avatar>
                            <Box>
                                <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>When to seek help</Typography>
                                <Typography variant="caption" color="text.secondary">Symptoms {'>'} 2 weeks or affecting daily life — talk to a provider.</Typography>
                            </Box>
                        </Box>
                    </Paper>
                    {/* Card 4 */}
                    <Paper elevation={1} sx={{ p: 2, borderRadius: 3, minWidth: 260, '&:hover': { boxShadow: 3 } }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                            <Avatar sx={{ bgcolor: 'rgba(254,202,202,0.8)', color: '#b91c1c' }}>
                                <WarningIcon />
                            </Avatar>
                            <Box>
                                <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>Urgent help</Typography>
                                <Typography variant="caption" color="text.secondary">If there are thoughts of harm, seek immediate emergency support.</Typography>
                            </Box>
                        </Box>
                    </Paper>
                </Box>
            </Box>
            {error && <Typography color="error" className={styles.errorMessage}>{error}</Typography> }
            
            <Paper elevation={2} className={styles.formPaper}>
                <form onSubmit={handleSubmit}>
                    {Object.keys(questions).map(key => (
                        <Box key={key} className={styles.formGroup} mb={2}>
                            <Typography variant="body1" component="label" htmlFor={key} mb={1}>
                                {questions[key].text}
                            </Typography>
                            {questions[key].type === 'number' ? (
                                <input
                                    id={key}
                                    type="number"
                                    value={answers[key] || ''}
                                    onChange={(e) => handleInputChange(key, e.target.value)}
                                    required
                                    className={styles.inputField}
                                />
                            ) : (
                                <select
                                    id={key}
                                    value={answers[key] || ''}
                                    onChange={(e) => handleInputChange(key, e.target.value)}
                                    required
                                    className={styles.selectField}
                                >
                                    <option value="">Select an answer</option>
                                    {questions[key].options.map(option => (
                                        <option key={option} value={option}>{option}</option>
                                    ))}
                                </select>
                            )}
                        </Box>
                    ))}
                    {/* Optional free-text field for user notes (sentiment-aware) */}
                    <Box mb={2}>
                        <Typography variant="body2" component="label" htmlFor="free-text" mb={1} sx={{ display: 'block', fontWeight: 500 }}>
                            Optional: Share your feelings in your own words
                        </Typography>
                        <textarea
                            id="free-text"
                            value={freeText}
                            onChange={(e) => setFreeText(e.target.value)}
                            placeholder="Write anything you'd like us to consider (e.g., sleep, worries, support)..."
                            rows={4}
                            className={styles.textareaField}
                            style={{ width: '100%', resize: 'vertical' }}
                        />
                        <Typography variant="caption" color="text.secondary">
                            We use privacy-preserving AI to analyze the sentiment of this text to improve risk accuracy. Do not include sensitive personal information.
                        </Typography>
                    </Box>

                    <Button type="submit" variant="contained" color="primary" disabled={loading} className={styles.submitButton}>
                        {loading ? <CircularProgress size={24} color="inherit" /> : 'Get Risk Analysis'}
                    </Button>
                </form>
            </Paper>

            {prediction !== null && assistance !== null && (
                <Paper elevation={2} className={`${styles.predictionResult} ${prediction === 'High Risk' ? styles.highRisk : ''}`} ref={resultsRef}>
                    <Typography variant="h5" component="h3" gutterBottom>
                        Analysis Result:
                    </Typography>
                    <Typography variant="body1" gutterBottom>
                        Your PPD risk is: <strong className={prediction === 'High Risk' ? styles.highRiskText : styles.lowRiskText}>{prediction}</strong>
                        {probability != null && ` (Probability: ${probability}%)`}
                    </Typography>

                    <Box mt={3}>
                        <Typography variant="h6" gutterBottom>
                            Recommendations and Assistance:
                        </Typography>
                        {assistance.recommendations.length > 0 ? (
                            <List>
                                {assistance.recommendations.map((rec, index) => (
                                    <ListItem key={index} disablePadding>
                                        <ListItemText primary={`• ${rec}`} />
                                    </ListItem>
                                ))}
                            </List>
                        ) : (
                            <Typography variant="body2">No specific recommendations available for this risk level.</Typography>
                        )}

                        {assistance.resources && assistance.resources.length > 0 && (
                            <Box mt={2}>
                                <Typography variant="h6" gutterBottom>
                                    Resources:
                                </Typography>
                                <List>
                                    {assistance.resources.map((res, index) => (
                                        <ListItem key={index} disablePadding>
                                            <ListItemText
                                                primary={res.name}
                                                secondary={
                                                    <>
                                                        {res.contact && `Contact: ${res.contact}`}
                                                        {res.contact && res.website && ' | '}
                                                        {res.website && <a href={res.website} target="_blank" rel="noopener noreferrer">Visit Website</a>}
                                                    </>
                                                }
                                            />
                                        </ListItem>
                                    ))}
                                </List>
                            </Box>
                        )}
                    </Box>

                    {/* Buttons to navigate to Mental Health page or Care Plan */}
                    <Box mt={3} sx={{ textAlign: 'center', display: 'flex', gap: 2, justifyContent: 'center' }}>
                         <Button 
                             variant="outlined" 
                             color="secondary" 
                             onClick={handleGoToMentalHealth}>
                           Go to Mental Health Dashboard
                         </Button>
                         <Button 
                            variant="contained" 
                            color="primary" 
                            onClick={() => navigate('/care-plan', { state: { ppdRisk: probability } })}>
                          Generate Personalized Care Plan
                        </Button>
                    </Box>

                </Paper>
            )}
        </div>
    );
};

export default PPDTestPage; 