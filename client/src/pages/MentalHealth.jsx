import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import styles from '../styles/MentalHealth.module.scss';
import { Box, Typography, Paper, TextField, Button, Select, MenuItem, FormControl, InputLabel, List, ListItem, ListItemText, CircularProgress, Link as MuiLink } from '@mui/material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';

const MentalHealth = () => {
  const { currentUser } = useAuth();
  const [mood, setMood] = useState(3);
  const [journalEntry, setJournalEntry] = useState('');
  const [showSupportDialog, setShowSupportDialog] = useState(false);
  const [recommendation, setRecommendation] = useState('');

  // --- Symptom Tracking State ---
  const [symptomName, setSymptomName] = useState('');
  const [symptomValue, setSymptomValue] = useState('');
  const [possibleSymptoms, setPossibleSymptoms] = useState([]);
  const [symptomHistory, setSymptomHistory] = useState([]);
  const [trackingLoading, setTrackingLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [trackingError, setTrackingError] = useState('');
  const [historyError, setHistoryError] = useState('');

  // --- Daily Check-in State and Handlers ---
  const [checkinHistory, setCheckinHistory] = useState([]);
  const [savingCheckin, setSavingCheckin] = useState(false);
  const [checkinError, setCheckinError] = useState('');
  const [checkinHistoryLoading, setCheckinHistoryLoading] = useState(false);
  const [checkinHistoryError, setCheckinHistoryError] = useState('');

  // --- Mood Chart Data Preparation ---
  const moodChartData = checkinHistory.slice().reverse().map(entry => ({
    date: new Date(entry.timestamp).toLocaleDateString(),
    mood: entry.mood
  }));

  // --- Detect 3+ consecutive days of low mood ---
  useEffect(() => {
    let consecutive = 0;
    let found = false;
    for (let i = 0; i < checkinHistory.length; i++) {
      if (checkinHistory[i].mood <= 2) {
        consecutive++;
        if (consecutive >= 3) {
          found = true;
          break;
        }
      } else {
        consecutive = 0;
      }
    }
    setShowSupportDialog(found);
  }, [checkinHistory]);

  // --- Personalized Recommendation Logic ---
  useEffect(() => {
    if (checkinHistory.length === 0) {
      setRecommendation('Remember to take a moment for yourself today. Even a short walk or a few deep breaths can help.');
      return;
    }
    const lastMood = checkinHistory[0].mood;
    const lastJournal = checkinHistory[0].journal_entry?.toLowerCase() || '';
    if (lastMood <= 2) {
      setRecommendation('You seem to be having a tough time. Try a short guided meditation or reach out to a loved one for support.');
    } else if (lastJournal.includes('tired') || lastJournal.includes('exhausted')) {
      setRecommendation('Rest is important. If possible, take a nap or ask for help with chores today.');
    } else if (lastJournal.includes('happy') || lastMood >= 4) {
      setRecommendation('You are doing great! Keep up the positive energy and celebrate small wins.');
    } else {
      setRecommendation('Keep tracking your mood and journaling. Consistency helps you and your care team spot trends.');
    }
  }, [checkinHistory]);

  // Fetch possible symptoms on component mount
  useEffect(() => {
    const fetchPossibleSymptoms = async () => {
      try {
        const token = localStorage.getItem('token');
        const response = await api.get('/symptom-tracking/all-possible-symptoms', {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        if (response.data && Array.isArray(response.data)) {
          setPossibleSymptoms(response.data);
          // Automatically select the first symptom if available
          if (response.data.length > 0) {
            setSymptomName(response.data[0]);
          }
        }
      } catch (err) {
        console.error('Error fetching possible symptoms:', err);
        // setTrackingError('Failed to load symptom list.'); // Optionally show error in UI
      }
    };
    fetchPossibleSymptoms();
  }, []); // Empty dependency array means this runs once on mount

  // Fetch symptom history when symptomName changes
  useEffect(() => {
    if (symptomName) {
      const fetchSymptomHistory = async () => {
        setHistoryLoading(true);
        setHistoryError('');
        try {
          const token = localStorage.getItem('token');
          const response = await api.get(`/symptom-tracking/history/${encodeURIComponent(symptomName)}`, {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          });
          if (response.data && Array.isArray(response.data)) {
            setSymptomHistory(response.data);
          }
        } catch (err) {
          console.error('Error fetching symptom history:', err);
          setHistoryError('Failed to load symptom history.');
        } finally {
          setHistoryLoading(false);
        }
      };
      fetchSymptomHistory();
    }
  }, [symptomName]); // Runs when selected symptom changes

  // Fetch daily check-in history on component mount
  useEffect(() => {
    const fetchCheckinHistory = async () => {
      if (!currentUser) return;
      setCheckinHistoryLoading(true);
      setCheckinHistoryError('');
      try {
        const token = localStorage.getItem('token');
        const response = await api.get('/daily-checkin/history', {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        if (response.data && Array.isArray(response.data)) {
          setCheckinHistory(response.data);
        }
      } catch (err) {
        console.error('Error fetching check-in history:', err);
        setCheckinHistoryError('Failed to load daily check-in history.');
      } finally {
        setCheckinHistoryLoading(false);
      }
    };
    fetchCheckinHistory();
  }, [currentUser]); // Runs when currentUser changes (on login/logout)

  const handleSymptomNameChange = (event) => {
    setSymptomName(event.target.value);
    setSymptomValue(''); // Clear value when symptom changes
  };

  const handleSymptomValueChange = (event) => {
    setSymptomValue(event.target.value);
  };

  const [symptomNote, setSymptomNote] = useState('');
  const [showSymptomAlert, setShowSymptomAlert] = useState(false);
  const [symptomInsight, setSymptomInsight] = useState('');

  // --- Symptom Chart Data Preparation ---
  const symptomChartData = symptomHistory.slice().reverse().map(entry => ({
    date: new Date(entry.timestamp).toLocaleDateString(),
    value: Number(entry.value),
    note: entry.note || ''
  }));

  // --- Smart Alert for High Symptom ---
  useEffect(() => {
    let consecutive = 0;
    let found = false;
    for (let i = 0; i < symptomHistory.length; i++) {
      if (Number(symptomHistory[i].value) >= 7) {
        consecutive++;
        if (consecutive >= 3) {
          found = true;
          break;
        }
      } else {
        consecutive = 0;
      }
    }
    setShowSymptomAlert(found);
  }, [symptomHistory]);

  // --- Correlation Insight (last 7 days) ---
  useEffect(() => {
    if (!symptomName || checkinHistory.length === 0 || symptomHistory.length === 0) {
      setSymptomInsight('');
      return;
    }
    // Get last 7 days for both mood and symptom
    const last7Mood = checkinHistory.slice(0, 7).map(e => ({ date: new Date(e.timestamp).toLocaleDateString(), mood: e.mood }));
    const last7Symptom = symptomHistory.slice(0, 7).map(e => ({ date: new Date(e.timestamp).toLocaleDateString(), value: Number(e.value) }));
    // Try to match by date
    let pairs = [];
    last7Mood.forEach(m => {
      const s = last7Symptom.find(e => e.date === m.date);
      if (s) pairs.push({ mood: m.mood, value: s.value });
    });
    if (pairs.length < 3) {
      setSymptomInsight('');
      return;
    }
    // Simple correlation: if mood is lower when symptom is higher
    const avgMoodHighSymptom = pairs.filter(p => p.value >= 7).reduce((a, b) => a + b.mood, 0) / (pairs.filter(p => p.value >= 7).length || 1);
    const avgMoodLowSymptom = pairs.filter(p => p.value < 7).reduce((a, b) => a + b.mood, 0) / (pairs.filter(p => p.value < 7).length || 1);
    if (avgMoodHighSymptom < avgMoodLowSymptom) {
      setSymptomInsight(`Your mood tends to be lower on days when '${symptomName}' is high. Consider addressing this symptom for better well-being.`);
    } else {
      setSymptomInsight('');
    }
  }, [symptomName, checkinHistory, symptomHistory]);

  const handleTrackSymptom = async () => {
    if (!symptomName || !symptomValue) {
      setTrackingError('Please select a symptom and enter a value.');
      return;
    }
    setTrackingLoading(true);
    setTrackingError('');

    try {
      const token = localStorage.getItem('token');
      await api.post('/symptom-tracking/track', {
        symptom_name: symptomName,
        value: symptomValue,
        note: symptomNote,
      }, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      // Clear input and refetch history after successful tracking
      setSymptomValue('');
      setSymptomNote('');
      // Trigger history fetch by updating symptomName state with current value
      // This ensures useEffect for history fetching runs
      // setSymptomName(symptomName); // Removed this line as it might not trigger useEffect
      // Alternative: manually call fetchSymptomHistory() here after a small delay or based on response success
      const response = await api.get(`/symptom-tracking/history/${encodeURIComponent(symptomName)}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (response.data && Array.isArray(response.data)) {
        setSymptomHistory(response.data);
      }

    } catch (err) {
      console.error('Error tracking symptom:', err);
      setTrackingError(err.response?.data?.msg || 'Failed to save symptom entry.');
    } finally {
      setTrackingLoading(false);
    }
  };

  const handleSaveDailyCheckin = async () => {
    if (!currentUser) return;
    setSavingCheckin(true);
    setCheckinError('');

    try {
      const token = localStorage.getItem('token');
      await api.post('/daily-checkin/save', {
        mood: mood,
        journal_entry: journalEntry,
      }, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      // Clear inputs after saving (optional, could keep for multi-save)
      // setMood(3); // Reset mood slider if desired
      // setJournalEntry(''); // Clear journal entry if desired
      alert('Daily check-in saved successfully!');
      // Refetch history after saving
      const tokenAfterSave = localStorage.getItem('token');
      const response = await api.get('/daily-checkin/history', {
        headers: {
          Authorization: `Bearer ${tokenAfterSave}`,
        },
      });
      if (response.data && Array.isArray(response.data)) {
        setCheckinHistory(response.data);
      }

    } catch (err) {
      console.error('Error saving daily check-in:', err);
      setCheckinError(err.response?.data?.msg || 'Failed to save daily check-in.');
    } finally {
      setSavingCheckin(false);
    }
  };

  return (
    <div className={styles.container}>
      <Typography variant="h4" component="h2" gutterBottom>
        Mental Health Dashboard
      </Typography>

      {/* Mood Trend Chart */}
      {checkinHistory.length > 0 && (
        <Paper elevation={2} className={styles.sectionPaper}>
          <Typography variant="h6" gutterBottom>Mood Trend</Typography>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={moodChartData} margin={{ top: 20, right: 30, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis domain={[1, 5]} ticks={[1,2,3,4,5]} tickFormatter={(t) => ({1:'😞',2:'🙁',3:'😐',4:'🙂',5:'😄'}[t] || t)} />
              <Tooltip />
              <Line type="monotone" dataKey="mood" stroke="#6c63ff" strokeWidth={3} dot={{ r: 5 }} />
            </LineChart>
          </ResponsiveContainer>
        </Paper>
      )}

      {/* Support Alert Popup */}
      <Dialog open={showSupportDialog} onClose={() => setShowSupportDialog(false)}>
        <DialogTitle>We're Here for You</DialogTitle>
        <DialogContent>
          <Typography>
            We've noticed you've been feeling low for a few days. Would you like to see some support resources or talk to a professional?
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowSupportDialog(false)} color="primary">Close</Button>
          <Button href="/resources" color="primary" variant="contained">View Resources</Button>
        </DialogActions>
      </Dialog>

      {/* Personalized Recommendation Card */}
      <Paper elevation={2} className={styles.sectionPaper}>
        <Typography variant="h6" gutterBottom>Today's Recommendation</Typography>
        <Typography variant="body1">{recommendation}</Typography>
      </Paper>

      {/* Existing Mood Tracking and Journal Section */}
      <Paper elevation={2} className={styles.sectionPaper}>
        <Typography variant="h5" gutterBottom>Mood Tracking & Journal</Typography>
        {/* Emoji mood picker replacing 1–5 slider */}
         <Box mb={3}>
             <Typography variant="h6" gutterBottom>How are you feeling today?</Typography>
             <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'nowrap' }}>
               {[
                 { v: 1, e: '😞', label: 'Very low' },
                 { v: 2, e: '🙁', label: 'Low' },
                 { v: 3, e: '😐', label: 'Neutral' },
                 { v: 4, e: '🙂', label: 'Good' },
                 { v: 5, e: '😄', label: 'Great' },
               ].map(({ v, e, label }) => (
                 <Button
                   key={v}
                   variant={mood === v ? 'contained' : 'outlined'}
                   color={mood === v ? 'primary' : 'inherit'}
                   onClick={() => setMood(v)}
                   aria-label={`${label} mood`}
                   sx={{ fontSize: 24, minWidth: 56, padding: '6px 12px', lineHeight: 1 }}
                 >
                   {e}
                 </Button>
               ))}
             </Box>
             <Typography variant="body2" sx={{ mt: 1 }}>
               Selected: {mood === 1 ? '😞 Very low' : mood === 2 ? '🙁 Low' : mood === 3 ? '😐 Neutral' : mood === 4 ? '🙂 Good' : '😄 Great'}
             </Typography>
         </Box>

         <Box mb={3}> {/* Added margin-bottom for spacing */}
             <Typography variant="h6" gutterBottom>Journal Entry</Typography>
             <TextField
                 label="Write about your day..."
                 multiline
                 rows={4}
                 fullWidth
                 value={journalEntry}
                 onChange={(e) => setJournalEntry(e.target.value)}
                 variant="outlined"
             />
         </Box>
         {/* Add a button to save mood/journal entry */}
         <Button
            variant="contained"
            color="primary"
            onClick={handleSaveDailyCheckin}
            disabled={savingCheckin}
         >
            {savingCheckin ? <CircularProgress size={24} color="inherit" /> : 'Save Mood & Journal'}
         </Button>
         {checkinError && <Typography color="error" sx={{ mt: 2 }}>{checkinError}</Typography>}
      </Paper>

      {/* --- Symptom Tracking Section --- */}
      <Paper elevation={2} className={styles.sectionPaper} sx={{ mt: 3 }}> {/* Added margin-top */}
        <Typography variant="h5" gutterBottom>Symptom Tracking</Typography>
        
        <Box mb={2}>
            <FormControl fullWidth>
                <InputLabel id="symptom-select-label">Select Symptom</InputLabel>
                <Select
                    labelId="symptom-select-label"
                    id="symptom-select"
                    value={symptomName}
                    label="Select Symptom"
                    onChange={handleSymptomNameChange}
                    disabled={possibleSymptoms.length === 0}
                >
                    {possibleSymptoms.length === 0 ? (
                         <MenuItem value="">Loading Symptoms...</MenuItem>
                    ) : (
                         possibleSymptoms.map(symptom => (
                            <MenuItem key={symptom} value={symptom}>{symptom}</MenuItem>
                         ))
                    )}
                </Select>
            </FormControl>
        </Box>

        {symptomName && (
            <Box mb={2}>
                <TextField
                    label={`Value for ${symptomName}`}
                    type="number"
                    value={symptomValue}
                    onChange={handleSymptomValueChange}
                    fullWidth
                    variant="outlined"
                />
                <TextField
                    label="Note (optional)"
                    value={symptomNote}
                    onChange={e => setSymptomNote(e.target.value)}
                    fullWidth
                    variant="outlined"
                    sx={{ mt: 2 }}
                />
            </Box>
        )}

        <Button 
            variant="contained" 
            color="primary" 
            onClick={handleTrackSymptom} 
            disabled={!symptomName || !symptomValue || trackingLoading}>
          {trackingLoading ? <CircularProgress size={24} color="inherit" /> : 'Track Symptom'}
        </Button>
        {trackingError && <Typography color="error" sx={{ mt: 2 }}>{trackingError}</Typography>}

        {/* Symptom Trend Chart */}
        {symptomName && symptomHistory.length > 0 && (
          <Box mt={4}>
            <Typography variant="h6" gutterBottom>Trend for {symptomName}</Typography>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={symptomChartData} margin={{ top: 20, right: 30, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip formatter={(value, name, props) => [`${value}${name === 'value' ? '' : ''}`, name]} />
                <Line type="monotone" dataKey="value" stroke="#e57373" strokeWidth={3} dot={{ r: 5 }} />
              </LineChart>
            </ResponsiveContainer>
          </Box>
        )}

        {/* Symptom Alert Popup */}
        <Dialog open={showSymptomAlert} onClose={() => setShowSymptomAlert(false)}>
          <DialogTitle>Take Care</DialogTitle>
          <DialogContent>
            <Typography>
              We've noticed '{symptomName}' has been high for a few days. Would you like to see some tips or talk to a professional?
            </Typography>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setShowSymptomAlert(false)} color="primary">Close</Button>
            <Button href="/resources" color="primary" variant="contained">View Resources</Button>
          </DialogActions>
        </Dialog>

        {/* Symptom & Mood Insight Card */}
        {symptomInsight && (
          <Paper elevation={2} className={styles.sectionPaper}>
            <Typography variant="h6" gutterBottom>Symptom & Mood Insight</Typography>
            <Typography variant="body1">{symptomInsight}</Typography>
          </Paper>
        )}

        {/* --- Symptom History and Chart Section --- */}
        {symptomName && (
            <Box mt={4}>
                <Typography variant="h6" gutterBottom>History for {symptomName}</Typography>
                {historyLoading ? (
                    <Box sx={{ display: 'flex', justifyContent: 'center' }}><CircularProgress size={24} /></Box>
                ) : historyError ? (
                    <Typography color="error">{historyError}</Typography>
                ) : symptomHistory.length > 0 ? (
                    <>
                        {/* Placeholder for Chart */}
                        {/* <Box className={styles.chartContainer}>*/}
                        {/*     <Line data={chartData} options={chartOptions} />*/}
                        {/* </Box>*/}
                        <List>
                            {symptomHistory.map((entry, index) => (
                                <ListItem key={index} disablePadding>
                                    <ListItemText 
                                        primary={`Value: ${entry.value}`}
                                        secondary={`Date: ${new Date(entry.timestamp).toLocaleDateString()} ${new Date(entry.timestamp).toLocaleTimeString()}`}
                                    />
                                </ListItem>
                            ))}
                        </List>
                    </>
                ) : (
                    <Typography>No history available for {symptomName}.</Typography>
                )}
            </Box>
        )}

      </Paper>

      {/* --- Daily Check-in History Section --- */}
      <Paper elevation={2} className={styles.sectionPaper} sx={{ mt: 3 }}>
        <Typography variant="h5" gutterBottom>Daily Check-in History</Typography>
        {checkinHistoryLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center' }}><CircularProgress size={24} /></Box>
        ) : checkinHistoryError ? (
            <Typography color="error">{checkinHistoryError}</Typography>
        ) : checkinHistory.length > 0 ? (
            <List>
                {checkinHistory.map((entry, index) => (
                  <ListItem key={index} disablePadding>
                        <ListItemText
                            primary={`Mood: ${entry.mood===1?'😞':entry.mood===2?'🙁':entry.mood===3?'😐':entry.mood===4?'🙂':'😄'} (${entry.mood})`}
                            secondary={
                              <>
                                  {`Journal: ${entry.journal_entry}`}<br/>{`Date: ${new Date(entry.timestamp).toLocaleDateString()} ${new Date(entry.timestamp).toLocaleTimeString()}`}</>
                              }
                          />
                    </ListItem>
                ))}
                </List>
            ) : (
                <Typography>No daily check-in history available.</Typography>
            )}
      </Paper>

      {/* --- Resources for Well-being Section --- */}
      <Paper elevation={2} className={styles.sectionPaper} sx={{ mt: 3 }}>
        <Typography variant="h5" gutterBottom>Resources for Well-being</Typography>
        <Box mb={2}>
          <Typography variant="h6" gutterBottom>Meditation & Yoga</Typography>
          <Typography variant="body1">Find guided meditations and gentle yoga practices to relax your mind and body.</Typography>
          <MuiLink href="https://www.youtube.com/results?search_query=guided+meditation+for+stress" target="_blank" rel="noopener noreferrer">Guided Meditation Videos</MuiLink><br/>
          <MuiLink href="https://www.youtube.com/results?search_query=postnatal+yoga" target="_blank" rel="noopener noreferrer">Postnatal Yoga Videos</MuiLink>
        </Box>

        <Box mb={2}>
          <Typography variant="h6" gutterBottom>Calming Videos</Typography>
          <Typography variant="body1">Watch soothing videos of nature or calming visuals.</Typography>
           <MuiLink href="https://www.youtube.com/results?search_query=calming+nature+sounds+and+visuals" target="_blank" rel="noopener noreferrer">Nature & Calming Videos</MuiLink>
        </Box>

        <Box>
          <Typography variant="h6" gutterBottom>Suggestion: Explore New Places</Typography>
          <Typography variant="body1">Sometimes a change of scenery can be refreshing. Consider a short trip to a peaceful local park, a nature trail, or a quiet spot nearby. Planning a small outing can be a positive distraction and provide a sense of adventure.</Typography>
           {/* You could add links to local parks/tourism boards here based on user location if available */}
           <MuiLink href="https://www.alltrails.com/" target="_blank" rel="noopener noreferrer">Find local trails and parks (Example)</MuiLink>
        </Box>
      </Paper>

      {/* Existing PPD Screening Section */}
      {/* Note: The PPD screening is currently on a separate page (PPDTestPage.jsx). 
           If you intended to move it here, that would be a separate step. */}
      {/* <Paper elevation={2} className={styles.sectionPaper} sx={{ mt: 3 }}>
        <Typography variant="h5" gutterBottom>PPD Screening</Typography>
        ... PPD screening questions and button (as seen on PPDTestPage) ...
      </Paper> */}

      {/* Existing Therapist Modal Trigger */}
      {/* <Button onClick={() => setShowTherapistModal(true)}>Find a Therapist</Button> */}
      {/* ... Therapist Modal component ... */}

    </div>
  );
};

export default MentalHealth;
