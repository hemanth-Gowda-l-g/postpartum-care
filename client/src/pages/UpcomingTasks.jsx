import React, { useState, useEffect, useCallback } from 'react';
import styles from '../styles/UpcomingTasks.module.scss';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import { Box, Typography, CircularProgress, Alert, Checkbox, FormControlLabel, IconButton, TextField, Paper } from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';

const UpcomingTasks = () => {
  const { currentUser } = useAuth();
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [newTaskTitle, setNewTaskTitle] = useState('');

  const fetchTasks = useCallback(async () => {
    if (!currentUser) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError('');
    try {
      const token = localStorage.getItem('token');
      const response = await api.get('/tasks', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      setTasks(response.data);
    } catch (err) {
      console.error('Error fetching tasks:', err);
      setError('Failed to load tasks. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [currentUser]);

  useEffect(() => {
    fetchTasks();
  }, [currentUser, fetchTasks]);

  const handleTaskComplete = async (taskId, completed) => {
    try {
      const token = localStorage.getItem('token');
      await api.put(`/tasks/${taskId}`, { completed: !completed }, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      setTasks(prevTasks =>
        prevTasks.map(task =>
          task.id === taskId ? { ...task, completed: !completed } : task
        )
      );
    } catch (err) {
      console.error('Error updating task:', err);
      setError('Failed to update task status.');
    }
  };

  const handleAddTask = async () => {
    if (!newTaskTitle.trim()) return;
    try {
      const token = localStorage.getItem('token');
      const response = await api.post('/tasks', {
        title: newTaskTitle.trim(),
        completed: false,
        time: new Date().toISOString(), // Placeholder for time
      }, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      setTasks(prevTasks => [...prevTasks, response.data]);
      setNewTaskTitle('');
    } catch (err) {
      console.error('Error adding task:', err);
      setError('Failed to add task.');
    }
  };

  const handleDeleteTask = async (taskId) => {
    try {
      const token = localStorage.getItem('token');
      await api.delete(`/tasks/${taskId}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      setTasks(prevTasks => prevTasks.filter(task => task.id !== taskId));
    } catch (err) {
      console.error('Error deleting task:', err);
      setError('Failed to delete task.');
    }
  };

  if (loading) {
    return (
      <Box className={styles.loadingContainer}>
        <CircularProgress />
        <Typography>Loading tasks...</Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Box className={styles.errorContainer}>
        <Alert severity="error">{error}</Alert>
      </Box>
    );
  }

  return (
    <div className={styles.upcomingTasks}>
      <Typography variant="h4" component="h2" gutterBottom>
        Your Progress & Tasks
      </Typography>

      {/* Add New Task Section */}
      <Box className={styles.addTaskSection} mb={3}>
        <TextField
          label="Add a new task"
          variant="outlined"
          fullWidth
          value={newTaskTitle}
          onChange={(e) => setNewTaskTitle(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleAddTask()}
        />
        <IconButton color="primary" onClick={handleAddTask} disabled={!newTaskTitle.trim()}>
          <AddIcon />
        </IconButton>
      </Box>

      {/* Task List */}
      <Box className={styles.taskList}>
        {tasks.length === 0 ? (
          <Typography variant="body1">No tasks found. Add a new task above!</Typography>
        ) : (
          tasks.map((task) => (
            <Paper key={task.id} className={styles.taskItem} elevation={1}>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={task.completed}
                    onChange={() => handleTaskComplete(task.id, task.completed)}
                    color="primary"
                  />
                }
                label={
                  <Typography variant="body1" className={task.completed ? styles.completedTask : ''}>
                    {task.title}
                  </Typography>
                }
              />
              <Typography variant="caption" color="textSecondary">
                {task.time ? new Date(task.time).toLocaleDateString() : 'No date'}
              </Typography>
              <IconButton edge="end" aria-label="delete" onClick={() => handleDeleteTask(task.id)}>
                <DeleteIcon />
              </IconButton>
            </Paper>
          ))
        )}
      </Box>

      {/* Future Enhancements: Progress Charts, Milestones, etc. */}
      <Box mt={5}>
        <Typography variant="h5" component="h3" gutterBottom>
          Progress Overview (Coming Soon!)
        </Typography>
        <Typography variant="body1" color="textSecondary">
          This section will feature charts and summaries of your mood, symptom, and task completion trends over time.
        </Typography>
      </Box>
    </div>
  );
};

export default UpcomingTasks;
