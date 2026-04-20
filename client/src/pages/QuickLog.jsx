import React, { useState } from 'react';
import styles from '../styles/QuickLog.module.scss';

const QuickLog = () => {
  const [logData, setLogData] = useState({
    mood: '',
    sleep: '',
    pain: '',
    notes: ''
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setLogData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    // TODO: Save log data
    console.log('Log data:', logData);
    setLogData({
      mood: '',
      sleep: '',
      pain: '',
      notes: ''
    });
  };

  return (
    <div className={styles.quickLog}>
      <h1>Quick Log</h1>
      <form onSubmit={handleSubmit} className={styles.logForm}>
        <div className={styles.formGroup}>
          <label htmlFor="mood">How are you feeling today?</label>
          <select
            id="mood"
            name="mood"
            value={logData.mood}
            onChange={handleChange}
            required
          >
            <option value="">Select mood</option>
            <option value="great">Great</option>
            <option value="good">Good</option>
            <option value="okay">Okay</option>
            <option value="low">Low</option>
          </select>
        </div>

        <div className={styles.formGroup}>
          <label htmlFor="sleep">How did you sleep?</label>
          <select
            id="sleep"
            name="sleep"
            value={logData.sleep}
            onChange={handleChange}
            required
          >
            <option value="">Select sleep quality</option>
            <option value="well">Well</option>
            <option value="okay">Okay</option>
            <option value="poor">Poor</option>
          </select>
        </div>

        <div className={styles.formGroup}>
          <label htmlFor="pain">Pain level (1-10)</label>
          <input
            type="range"
            id="pain"
            name="pain"
            min="1"
            max="10"
            value={logData.pain}
            onChange={handleChange}
          />
          <span className={styles.painValue}>{logData.pain || '5'}</span>
        </div>

        <div className={styles.formGroup}>
          <label htmlFor="notes">Additional Notes</label>
          <textarea
            id="notes"
            name="notes"
            value={logData.notes}
            onChange={handleChange}
            rows="4"
          />
        </div>

        <button type="submit" className={styles.submitButton}>
          Save Log
        </button>
      </form>
    </div>
  );
};

export default QuickLog; 