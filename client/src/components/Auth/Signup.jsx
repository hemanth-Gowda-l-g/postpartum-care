import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ReactComponent as DoctorIcon } from '../../assets/icons/doctor.svg';
import styles from '../../styles/Auth.module.scss';
import axios from 'axios';

const Signup = () => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
    deliveryType: '',
    dueDate: '',
    conditions: []
  });

  const [step, setStep] = useState(1);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleConditionToggle = (condition) => {
    setFormData(prev => ({
      ...prev,
      conditions: prev.conditions.includes(condition)
        ? prev.conditions.filter(c => c !== condition)
        : [...prev.conditions, condition]
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (step < 3) {
      setStep(step + 1);
      return;
    }

    // Validate passwords match
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await axios.post('http://localhost:5000/api/auth/register', {
        email: formData.email,
        password: formData.password,
        name: formData.name,
        role: 'mother',
        deliveryType: formData.deliveryType,
        dueDate: formData.dueDate,
        conditions: formData.conditions
      });

      // Store the token and user data
      localStorage.setItem('token', response.data.access_token);
      localStorage.setItem('user', JSON.stringify(response.data.user));

      // Navigate to onboarding
      navigate('/onboarding');
    } catch (err) {
      setError(err.response?.data?.msg || 'Failed to create account');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.authContainer}>
      <div className={styles.authCard}>
        <div className={styles.authHeader}>
          <DoctorIcon className={styles.authIcon} />
          <h2>Create Your Account</h2>
          <p>Step {step} of 3</p>
        </div>

        {error && <div className={styles.errorMessage}>{error}</div>}

        <form onSubmit={handleSubmit}>
          {step === 1 && (
            <div className={styles.step}>
              <div className={styles.formGroup}>
                <label>Full Name</label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  required
                />
              </div>
              <div className={styles.formGroup}>
                <label>Email</label>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  required
                />
              </div>
              <div className={styles.formGroup}>
                <label>Password</label>
                <input
                  type="password"
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  required
                />
              </div>
              <div className={styles.formGroup}>
                <label>Confirm Password</label>
                <input
                  type="password"
                  name="confirmPassword"
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  required
                />
              </div>
            </div>
          )}

          {step === 2 && (
            <div className={styles.step}>
              <div className={styles.formGroup}>
                <label>Delivery Type</label>
                <select
                  name="deliveryType"
                  value={formData.deliveryType}
                  onChange={handleChange}
                  required
                >
                  <option value="">Select...</option>
                  <option value="vaginal">Vaginal Delivery</option>
                  <option value="c-section">C-Section</option>
                  <option value="vbac">VBAC</option>
                  <option value="assisted">Assisted Vaginal</option>
                </select>
              </div>
              <div className={styles.formGroup}>
                <label>Delivery/Due Date</label>
                <input
                  type="date"
                  name="dueDate"
                  value={formData.dueDate}
                  onChange={handleChange}
                  required
                />
              </div>
            </div>
          )}

          {step === 3 && (
            <div className={styles.step}>
              <h4>Pre-existing Conditions</h4>
              <div className={styles.conditionGrid}>
                {['Diabetes', 'Hypertension', 'Thyroid', 'Anemia', 'Depression', 'None'].map(condition => (
                  <div
                    key={condition}
                    className={`${styles.conditionCard} ${formData.conditions.includes(condition) ? styles.selected : ''}`}
                    onClick={() => handleConditionToggle(condition)}
                  >
                    {condition}
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className={styles.authActions}>
            {step > 1 && (
              <button
                type="button"
                className={styles.secondaryButton}
                onClick={() => setStep(step - 1)}
              >
                Back
              </button>
            )}
            <button type="submit" className={styles.primaryButton} disabled={loading}>
              {step < 3 ? 'Continue' : 'Complete Signup'}
            </button>
          </div>
        </form>

        <div className={styles.authFooter}>
          Already have an account? <Link to="/login">Log in</Link>
        </div>
      </div>
    </div>
  );
};

export default Signup;