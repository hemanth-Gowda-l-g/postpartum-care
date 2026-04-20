import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Box, Button, Card, CardContent, Chip, Divider, Grid, MenuItem, Select, Snackbar, Stack, TextField, Typography, Alert, LinearProgress, List, ListItem, ListItemText, Tooltip, IconButton, Slider, Fab } from '@mui/material';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import StopIcon from '@mui/icons-material/Stop';
import WaterDropIcon from '@mui/icons-material/WaterDrop';
import LocalHospitalIcon from '@mui/icons-material/LocalHospital';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import ScheduleIcon from '@mui/icons-material/Schedule';
import AvTimerIcon from '@mui/icons-material/AvTimer';
import AlarmIcon from '@mui/icons-material/Alarm';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';

function formatDuration(sec) {
  if (!sec && sec !== 0) return '-';
  const m = Math.floor(sec / 60);
  const s = sec % 60;
  return `${m}m ${s}s`;
}

export default function BreastfeedingTracker() {
  const { currentUser } = useAuth();
  const userId = currentUser?.user_id || currentUser?._id || currentUser?.id || currentUser?.uid;
  const [sessionId, setSessionId] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  const [startTs, setStartTs] = useState(null);
  const [elapsed, setElapsed] = useState(0);

  const [leftSec, setLeftSec] = useState(0);
  const [rightSec, setRightSec] = useState(0);
  const [activeSide, setActiveSide] = useState(null); // 'left' | 'right' | null

  const [type, setType] = useState('breast');
  const [bottleAmount, setBottleAmount] = useState('');
  const [mood, setMood] = useState(5);
  const [pain, setPain] = useState(0);
  const [behavior, setBehavior] = useState('content');
  const [notes, setNotes] = useState('');

  const [summary, setSummary] = useState(null);
  const [reminder, setReminder] = useState(null);
  const [history, setHistory] = useState([]);
  const [showHydration, setShowHydration] = useState(false);
  const timerRef = useRef(null);
  const sideTimerRef = useRef(null);
  const [, setIsPaused] = useState(false);
  const [preSide, setPreSide] = useState('left');
  const [sleepMinutes, setSleepMinutes] = useState('');

  // Diaper log UI (one-tap buttons; no local counters)
  const [diaperSummary, setDiaperSummary] = useState(null);

  // Weight log UI
  const [weightKg, setWeightKg] = useState('');
  const [recordedAt, setRecordedAt] = useState(() => new Date().toISOString().slice(0,16)); // yyyy-MM-ddTHH:mm


  const fetchSummary = useCallback(async () => {
    try {
      const res = await api.get('/breastfeeding/feed/summary', {
        params: userId ? { user_id: userId } : {},
      });
      setSummary(res.data);
    } catch (e) {
      console.error('feed/summary error', e);
    }
  }, [userId]);

  // (fetchHistory removed; using fetchHistoryWithRange instead)

  // (local-day range helper removed; default server window is used for history)

  // Default history fetch (server decides the day window; aligns with summary)
  const fetchHistoryDefault = useCallback(async () => {
    try {
      const res = await api.get('/breastfeeding/feed/history', {
        params: userId ? { user_id: userId } : {},
      });
      console.debug('feed/history default response', res.data);
      const d = res.data;
      let items = [];
      if (Array.isArray(d)) items = d;
      else if (Array.isArray(d?.items)) items = d.items;
      else if (Array.isArray(d?.data?.items)) items = d.data.items;
      else if (Array.isArray(d?.result?.items)) items = d.result.items;
      else if (Array.isArray(d?.results)) items = d.results;
      else if (d && typeof d === 'object') {
        // Last resort: pick the first array value in the object
        const firstArray = Object.values(d).find(v => Array.isArray(v));
        if (firstArray) items = firstArray;
      }
      setHistory(items);
    } catch (e) {
      console.error('feed/history (default) error', e);
    }
  }, [userId]);

  // (fetchHistoryWithRange removed; using fetchHistoryDefault only)

  // Fetch diaper daily summary
  const fetchDiaperSummary = useCallback(async () => {
    try {
      const res = await api.get('/breastfeeding/diaper/summary', {
        params: userId ? { user_id: userId } : {},
      });
      setDiaperSummary(res.data);
    } catch (e) {
      console.error('diaper/summary error', e);
    }
  }, [userId]);

  // Quick one-tap logs
  const logWetOnce = async () => {
    try {
      const payload = { wet_count: 1, dirty_count: 0 };
      await api.post('/breastfeeding/diaper', userId ? { user_id: userId, ...payload } : payload);
      await fetchDiaperSummary();
    } catch (e) {
      console.error('log wet error', e);
    }
  };

  const logDirtyOnce = async () => {
    try {
      const payload = { wet_count: 0, dirty_count: 1 };
      await api.post('/breastfeeding/diaper', userId ? { user_id: userId, ...payload } : payload);
      await fetchDiaperSummary();
    } catch (e) {
      console.error('log dirty error', e);
    }
  };

  const logWeight = async () => {
    try {
      const payload = { weight_kg: Number(weightKg), recorded_at: new Date(recordedAt).toISOString() };
      await api.post('/breastfeeding/weight', userId ? { user_id: userId, ...payload } : payload);
      setWeightKg('');
    } catch (e) {
      console.error('log weight error', e);
    }
  };

  const computeInsights = () => {
    const insights = [];
    const count = summary?.count || 0;
    const totalSec = summary?.total_duration_sec || 0;
    if (count < 8) insights.push(`Target 8 feeds/day – you've logged ${count}.`);
    // Evening longer feeds heuristic
    const evening = history.filter(h => new Date(h.started_at).getHours() >= 18);
    const eveAvg = evening.length ? evening.reduce((a,b)=>a+(b.duration_sec||0),0)/evening.length : 0;
    const dayRest = history.filter(h => new Date(h.started_at).getHours() < 18);
    const dayAvg = dayRest.length ? dayRest.reduce((a,b)=>a+(b.duration_sec||0),0)/dayRest.length : 0;
    if (eveAvg > 1.2 * dayAvg && eveAvg > 0) insights.push('Baby usually feeds longer in the evening.');
    // Short feed flag (<7 minutes average)
    const overallAvg = count ? totalSec / count : 0;
    if (overallAvg > 0 && overallAvg < 7*60) insights.push('Consider consulting lactation support; feeding durations are shorter than average.');
    // Diaper hydration heuristic
    if ((diaperSummary?.wet_total || 0) >= 6) insights.push('Great hydration: 6+ wet diapers today.');
    return insights;
  };

  const fetchReminders = useCallback(async () => {
    try {
      const res = await api.get('/breastfeeding/reminders', {
        params: userId ? { user_id: userId } : {},
      });
      setReminder(res.data);
    } catch (e) {
      console.error('reminders error', e);
    }
  }, [userId]);

  // Load initial data and refresh reminders every minute
  useEffect(() => {
    if (!userId) return; // wait for auth
    fetchSummary();
    fetchReminders();
    // Hotfix: use default (server) window for history so it matches summary reliably
    fetchHistoryDefault();
    fetchDiaperSummary();
    const id = setInterval(fetchReminders, 60000);
    return () => clearInterval(id);
  }, [userId, fetchSummary, fetchReminders, fetchHistoryDefault, fetchDiaperSummary]);

  const start = async () => {
    try {
      const res = await api.post('/breastfeeding/feed/start', userId ? { user_id: userId } : {});
      setSessionId(res.data.session_id);
      setIsRunning(true);
      const now = Date.now();
      setStartTs(now);
      timerRef.current = setInterval(() => setElapsed(Math.floor((Date.now() - now) / 1000)), 1000);
      // initialize side as left by default for quick start
      const initialSide = preSide || 'left';
      setActiveSide(initialSide);
      sideTimerRef.current = setInterval(() => {
        if (initialSide === 'left') setLeftSec(prev => prev + 1);
        else setRightSec(prev => prev + 1);
      }, 1000);
    } catch (e) {
      console.error('feed/start error', e);
      setShowHydration(false);
    }
  };

  useEffect(() => {
    if (!isRunning) return;
    // keep elapsed in sync
    const t = setInterval(() => setElapsed(Math.floor((Date.now() - startTs) / 1000)), 1000);
    return () => clearInterval(t);
  }, [isRunning, startTs]);

  const switchSide = (side) => {
    if (!isRunning) return;
    if (activeSide === side) return;
    // clear previous
    if (sideTimerRef.current) clearInterval(sideTimerRef.current);
    setActiveSide(side);
    sideTimerRef.current = setInterval(() => {
      if (side === 'left') setLeftSec(prev => prev + 1);
      else setRightSec(prev => prev + 1);
    }, 1000);
  };

  const stop = async () => {
    if (sideTimerRef.current) clearInterval(sideTimerRef.current);
    if (timerRef.current) clearInterval(timerRef.current);
    setIsRunning(false);
    const totalSec = leftSec + rightSec || elapsed || 0;
    const payload = {
      session_id: sessionId,
      type,
      bottle_amount_ml: type !== 'breast' ? Number(bottleAmount || 0) : undefined,
      mood: Number(mood),
      pain_level: Number(pain),
      baby_behavior: behavior,
      notes,
      sleep_after_min: sleepMinutes !== '' ? Number(sleepMinutes) : undefined,
      sides: [
        { side: 'left', duration_sec: leftSec },
        { side: 'right', duration_sec: rightSec },
      ],
    };
    await api.post('/breastfeeding/feed/stop', userId ? { user_id: userId, ...payload } : payload);
    // Hydration nudge if long feed (>= 45 min)
    if (totalSec >= 45 * 60) {
      setShowHydration(true);
    }
    setSessionId(null);
    setElapsed(0);
    setLeftSec(0);
    setRightSec(0);
    setActiveSide(null);
    setIsPaused(false);
    setSleepMinutes('');
    await fetchSummary();
    await fetchReminders();
    // Keep history consistent with summary right after stop
    await fetchHistoryDefault();
    await fetchDiaperSummary();
  };

  const totalSide = leftSec + rightSec;

  return (
    <>
    <Box sx={{ bgcolor: '#f9f7fc', minHeight: '100vh', pb: 3 }}>
      <Typography variant="h5" sx={{ mb: 2 }}>Breastfeeding Tracker</Typography>
      <Grid container spacing={2}>
        <Grid item xs={12} md={6}>
          <Card sx={{ borderRadius: 3, boxShadow: 3 }}>
            <CardContent sx={{ position: 'relative' }}>
              <Stack spacing={2} alignItems="center">
                <Box textAlign="center">
                  <Typography variant="overline">Current Session</Typography>
                  <Typography variant="h3" sx={{ color: '#6C63FF', fontWeight: 700 }}>{formatDuration(totalSide || elapsed)}</Typography>
                  {isRunning && reminder?.since_last_feed_min != null && (
                    <Typography variant="caption" color="text.secondary">Last feed {reminder.since_last_feed_min} min ago</Typography>
                  )}
                </Box>
                {/* Floating start/stop */}
                <Box sx={{ position: 'absolute', top: 8, right: 8 }}>
                  {!isRunning ? (
                    <Fab color="primary" size="medium" onClick={start} disabled={!userId}>
                      <PlayArrowIcon />
                    </Fab>
                  ) : (
                    <Fab color="error" size="medium" onClick={stop}>
                      <StopIcon />
                    </Fab>
                  )}
                </Box>
              </Stack>

              <Divider sx={{ my: 2 }} />

              {/* Pre-session big side toggle */}
              {!isRunning && (
                <Stack direction="row" spacing={2} sx={{ mb: 2 }}>
                  <Button variant={preSide==='left' ? 'contained' : 'outlined'} onClick={() => setPreSide('left')} fullWidth size="large">Left</Button>
                  <Button variant={preSide==='right' ? 'contained' : 'outlined'} onClick={() => setPreSide('right')} fullWidth size="large">Right</Button>
                </Stack>
              )}

              <Grid container spacing={2} sx={{ mb: 1 }}>
                <Grid item xs={12} sm={6}>
                  <Button fullWidth size="large" variant={activeSide==='left'?'contained':'outlined'} color="primary" onClick={() => switchSide('left')}>LEFT</Button>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Button fullWidth size="large" variant={activeSide==='right'?'contained':'outlined'} color="success" onClick={() => switchSide('right')}>RIGHT</Button>
                </Grid>
              </Grid>

              <Divider sx={{ my: 2 }} />

              <Grid container spacing={2} alignItems="center">
                <Grid item xs={12} sm={6} md={2.4}>
                  <Select fullWidth size="small" value={type} onChange={(e) => setType(e.target.value)}>
                    <MenuItem value="breast">Breast</MenuItem>
                    <MenuItem value="formula">Formula</MenuItem>
                    <MenuItem value="pumped">Pumped Milk</MenuItem>
                    <MenuItem value="combo">Combo</MenuItem>
                  </Select>
                </Grid>
                {(type !== 'breast') && (
                  <Grid item xs={12} sm={6} md={2.4}>
                    <TextField type="number" size="small" fullWidth label="Amount (ml)" value={bottleAmount} onChange={(e) => setBottleAmount(e.target.value)} />
                  </Grid>
                )}
                <Grid item xs={6} sm={3} md={2.4}>
                  <TextField type="number" size="small" fullWidth label="Mood (1-5)" value={mood} onChange={(e) => setMood(e.target.value)} />
                </Grid>
                <Grid item xs={12} sm={6} md={3.6}>
                  <Typography variant="caption" sx={{ display: 'block', color: 'text.secondary' }}>Pain (0–10)</Typography>
                  <Slider value={Number(pain)} min={0} max={10} step={1} onChange={(_, v) => setPain(v)} sx={{ mt: -0.5 }} />
                </Grid>
                <Grid item xs={12} sm={6} md={2.4}>
                  <Stack direction="row" spacing={1} alignItems="center">
                    <Select fullWidth size="small" value={behavior} onChange={(e) => setBehavior(e.target.value)} sx={{ flexGrow: 1 }}>
                      <MenuItem value="content">Content</MenuItem>
                      <MenuItem value="fussy">Fussy</MenuItem>
                      <MenuItem value="spit_up">Spit-up</MenuItem>
                      <MenuItem value="asleep">Fell asleep</MenuItem>
                    </Select>
                    <Tooltip title="Baby's behavior after feeding. 'Content' suggests satiety; 'Fussy' may indicate more hunger or discomfort.">
                      <IconButton size="small" aria-label="behavior info">
                        <InfoOutlinedIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </Stack>
                </Grid>
                <Grid item xs={12} md={3.6}>
                  <TextField size="small" fullWidth label="Notes" value={notes} onChange={(e) => setNotes(e.target.value)} />
                </Grid>
                {!isRunning && (
                  <Grid item xs={12} sm={6} md={2.4}>
                    <TextField type="number" size="small" fullWidth label="Sleep after feed (min)" value={sleepMinutes} onChange={(e) => setSleepMinutes(e.target.value)} />
                  </Grid>
                )}
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card sx={{ borderRadius: 3, boxShadow: 3 }}>
            <CardContent>
              <Typography variant="overline">Today Summary</Typography>
              <Grid container spacing={2} sx={{ mt: 1 }}>
                <Grid item xs={6} sm={3}>
                  <Stack direction="row" spacing={1} alignItems="center">
                    <AvTimerIcon color="primary" />
                    <Box>
                      <Typography variant="caption" color="text.secondary">Feeds</Typography>
                      <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>{summary?.count ?? 0}</Typography>
                    </Box>
                  </Stack>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Stack direction="row" spacing={1} alignItems="center">
                    <AccessTimeIcon color="primary" />
                    <Box>
                      <Typography variant="caption" color="text.secondary">Total Duration</Typography>
                      <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>{formatDuration(summary?.total_duration_sec)}</Typography>
                    </Box>
                  </Stack>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Stack direction="row" spacing={1} alignItems="center">
                    <ScheduleIcon color="primary" />
                    <Box>
                      <Typography variant="caption" color="text.secondary">Avg Gap</Typography>
                      <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>{summary?.avg_gap_sec ? formatDuration(Math.floor(summary.avg_gap_sec)) : '-'}</Typography>
                    </Box>
                  </Stack>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Stack direction="row" spacing={1} alignItems="center">
                    <AlarmIcon color="primary" />
                    <Box>
                      <Typography variant="caption" color="text.secondary">Peak Hour</Typography>
                      <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>{summary?.cluster_hour != null ? `${summary.cluster_hour}:00` : '-'}</Typography>
                    </Box>
                  </Stack>
                </Grid>
              </Grid>
              {/* Averages row: Mood, Pain, Sleep */}
              <Grid container spacing={2} sx={{ mt: 1 }}>
                <Grid item xs={4}>
                  <Typography variant="caption" color="text.secondary">Avg Mood</Typography>
                  <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>{summary?.avg_mood != null ? Number(summary.avg_mood).toFixed(1) : '-'}</Typography>
                </Grid>
                <Grid item xs={4}>
                  <Typography variant="caption" color="text.secondary">Avg Pain</Typography>
                  <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>{summary?.avg_pain != null ? Number(summary.avg_pain).toFixed(1) : '-'}</Typography>
                </Grid>
                <Grid item xs={4}>
                  <Typography variant="caption" color="text.secondary">Avg Sleep After (min)</Typography>
                  <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>{summary?.avg_sleep_after_min != null ? Math.round(summary.avg_sleep_after_min) : '-'}</Typography>
                </Grid>
              </Grid>
              <Box sx={{ mt: 2 }}>
                <Typography variant="body2">Goal progress: {Math.min(summary?.count || 0,8)}/8 feeds</Typography>
                <LinearProgress variant="determinate" value={Math.min(((summary?.count || 0)/8)*100,100)} sx={{ mt: 0.5, height: 8, borderRadius: 5 }} />
              </Box>
              <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
                <Chip icon={<WaterDropIcon />} label="Hydration" variant="outlined" sx={{ borderRadius: 999 }} />
                <Chip icon={<LocalHospitalIcon />} label="Lactation support" variant="outlined" sx={{ borderRadius: 999 }} />
              </Stack>

              <Divider sx={{ my: 2 }} />
              <Typography variant="overline">Smart Insights</Typography>
              <Box sx={{ mt: 1, p: 2, bgcolor: '#FFF9C4', borderRadius: 2 }}>
                {computeInsights().length ? (
                  <Stack spacing={0.5}>
                    {computeInsights().map((i, idx) => (
                      <Stack key={idx} direction="row" spacing={1} alignItems="flex-start">
                        <span style={{ lineHeight: 1.8 }}>{idx === 0 ? '⚠️' : '💡'}</span>
                        <Typography variant="body2">{i}</Typography>
                      </Stack>
                    ))}
                  </Stack>
                ) : (
                  <Typography variant="body2" color="text.secondary">No insights yet. Log a few feeds to see trends.</Typography>
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Simple timeline (list) of today's feeds) — hide when no items */}
        {history?.length > 0 && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="overline">Today's Feed Timeline</Typography>
                <List dense>
                  {history.map((h, idx) => (
                    <ListItem key={idx} divider>
                      <ListItemText
                        primary={`${new Date(h.started_at).toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})} • ${formatDuration(h.duration_sec || 0)}`}
                        secondary={`Sides: ${(h.sides||[]).map(s=>`${s.side[0].toUpperCase()}: ${formatDuration(s.duration_sec||0)}`).join('  ')}${h.type?` • Type: ${h.type}`:''}`}
                      />
                    </ListItem>
                  ))}
                </List>
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* Diaper log and summary */}
        <Grid item xs={12} md={6}>
          <Card sx={{ borderRadius: 3, boxShadow: 3 }}>
            <CardContent>
              <Typography variant="overline">Diaper Log</Typography>
              <Grid container spacing={2} alignItems="center" sx={{ mt: 1 }}>
                <Grid item xs={6}>
                  <Button onClick={logWetOnce} fullWidth variant="contained" color="primary" sx={{ borderRadius: 999, py: 1.2 }}>Wet</Button>
                  <Typography align="center" variant="caption" sx={{ mt: 0.5, display: 'block' }}>
                    {`Today: ${diaperSummary?.wet_total ?? 0}`}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Button onClick={logDirtyOnce} fullWidth variant="contained" color="success" sx={{ borderRadius: 999, py: 1.2 }}>Dirty</Button>
                  <Typography align="center" variant="caption" sx={{ mt: 0.5, display: 'block' }}>
                    {`Today: ${diaperSummary?.dirty_total ?? 0}`}
                  </Typography>
                </Grid>
              </Grid>
              <Divider sx={{ my: 1.5 }} />
              <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-start' }}>
                <InfoOutlinedIcon color="action" sx={{ mt: 0.3 }} />
                <Box>
                  <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>Why track diapers?</Typography>
                  <Typography variant="body2" color="text.secondary">
                    • Wet diapers reflect hydration. After day 5, aim for ~6+ wet diapers/day.<br />
                    • Dirty diapers show milk intake. Early weeks: 3–4+ yellow, seedy stools/day (breastfed).<br />
                    • Seek care if fewer than 4 wet diapers in 24h, dark urine, brick‑dust stains, no stool {'>'} 24–48h (early weeks),
                      or signs of dehydration (lethargy, dry mouth, sunken soft spot).
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Weight log */}
        <Grid item xs={12} md={6}>
          <Card sx={{ borderRadius: 3, boxShadow: 3 }}>
            <CardContent>
              <Typography variant="overline">Growth Log (Weight)</Typography>
              <Grid container spacing={2} alignItems="center" sx={{ mt: 1 }}>
                <Grid item xs={12} md={4}>
                  <TextField type="number" size="small" fullWidth label="Weight (kg)" value={weightKg} onChange={(e)=>setWeightKg(e.target.value)} />
                </Grid>
                <Grid item xs={12} md={5}>
                  <TextField type="datetime-local" size="small" fullWidth label="Recorded At" value={recordedAt} onChange={(e)=>setRecordedAt(e.target.value)} />
                </Grid>
                <Grid item xs={12} md={3} sx={{ textAlign: { xs: 'left', md: 'right' } }}>
                  <Button variant="contained" onClick={logWeight} disabled={!userId || !weightKg} sx={{ borderRadius: 2 }}>Log Weight</Button>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
    <Snackbar
      open={showHydration}
      autoHideDuration={6000}
      onClose={() => setShowHydration(false)}
      anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
    >
      <Alert onClose={() => setShowHydration(false)} severity="info" sx={{ width: '100%' }}>
        Long feed completed. Remember to drink a large glass of water to stay hydrated! 💧
      </Alert>
    </Snackbar>
  </>
  );
}
