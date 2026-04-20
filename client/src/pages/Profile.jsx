import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import { Box, Typography, Paper, TextField, Button, CircularProgress, MenuItem } from '@mui/material';

const Profile = () => {
  const { logout } = useAuth();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    const fetchProfile = async () => {
      setLoading(true);
      setError('');
      try {
        const token = localStorage.getItem('token');
        const response = await api.get('/auth/me', {
          headers: { Authorization: `Bearer ${token}` },
        });
        setProfile(response.data);
      } catch (err) {
        setError('Failed to load profile.');
      } finally {
        setLoading(false);
      }
    };
    fetchProfile();
  }, []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setProfile((prev) => ({ ...prev, [name]: value }));
  };

  const handleSave = async () => {
    setSaving(true);
    setError('');
    setSuccess('');
    try {
      const token = localStorage.getItem('token');
      await api.put('/auth/update', profile, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setSuccess('Profile updated successfully!');
    } catch (err) {
      setError('Failed to update profile.');
    } finally {
      setSaving(false);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  if (loading) {
    return <Box sx={{ display: 'flex', justifyContent: 'center', mt: 8 }}><CircularProgress /></Box>;
  }
  if (!profile) {
    return <Typography color="error">{error || 'No profile data.'}</Typography>;
  }

  return (
    <Box sx={{ maxWidth: 500, mx: 'auto', mt: 6 }}>
      <Paper sx={{ p: 4 }}>
        <Typography variant="h4" gutterBottom>Profile</Typography>
        <TextField
          label="Name"
          name="name"
          value={profile.name || ''}
          onChange={handleChange}
          fullWidth
          margin="normal"
        />
        <TextField
          label="Email"
          name="email"
          value={profile.email || ''}
          fullWidth
          margin="normal"
          disabled
        />
        <TextField
          label="Role"
          name="role"
          value={profile.role || ''}
          fullWidth
          margin="normal"
          disabled
        />
        <TextField
          label="Delivery Type"
          name="delivery_type"
          value={profile.delivery_type || ''}
          onChange={handleChange}
          select
          fullWidth
          margin="normal"
        >
          <MenuItem value="vaginal">Vaginal</MenuItem>
          <MenuItem value="cesarean">Cesarean</MenuItem>
        </TextField>
        <TextField
          label="Due Date"
          name="due_date"
          type="date"
          value={profile.due_date || ''}
          onChange={handleChange}
          fullWidth
          margin="normal"
          InputLabelProps={{ shrink: true }}
        />
        <TextField
          label="Conditions (comma separated)"
          name="conditions"
          value={Array.isArray(profile.conditions) ? profile.conditions.join(', ') : (profile.conditions || '')}
          onChange={e => setProfile(prev => ({ ...prev, conditions: e.target.value.split(',').map(s => s.trim()) }))}
          fullWidth
          margin="normal"
        />
        <Box mt={2} display="flex" gap={2}>
          <Button variant="contained" color="primary" onClick={handleSave} disabled={saving}>
            {saving ? <CircularProgress size={20} color="inherit" /> : 'Save'}
          </Button>
          <Button variant="outlined" color="secondary" onClick={handleLogout}>Log Out</Button>
        </Box>
        {error && <Typography color="error" sx={{ mt: 2 }}>{error}</Typography>}
        {success && <Typography color="primary" sx={{ mt: 2 }}>{success}</Typography>}
      </Paper>
    </Box>
  );
};

export default Profile; 