import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
// import { motion } from 'framer-motion';
import { ReactComponent as HeartIcon } from '../../assets/icons/heart.svg';
// import loginIllustration from '../../assets/illustrations/login-mom-baby.png'; // Placeholder image path
import styles from '../../styles/Auth.module.scss'; // Revert to Auth styles
import axios from 'axios';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      const response = await axios.post('http://localhost:5000/api/auth/login', {
        email,
        password
      });

      // Use the auth context to handle login
      login(response.data.user, response.data.access_token);

      // Navigate based on user role
      const userRole = response.data.user.role;
      switch (userRole) {
        case 'admin':
          navigate('/admin-dashboard');
          break;
        case 'healthcare_provider':
        case 'mental_health_specialist':
          navigate('/provider-dashboard');
          break;
        case 'mother':
        default:
          navigate('/dashboard');
          break;
      }
    } catch (err) {
      setError(err.response?.data?.msg || 'Invalid email or password');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.authContainer}> { /* Revert to Auth styles */}
      <div className={styles.authCard}>
        <div className={styles.authHeader}>
          <HeartIcon className={styles.authIcon} />
          <h2>Welcome Back</h2>
          <p>Log in to continue your recovery journey</p>
        </div>

        {error && <div className={styles.errorMessage}>{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className={styles.formGroup}>
            <label htmlFor="email">Email</label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div className={styles.formGroup}>
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <div className={styles.forgotPassword}>
            <Link to="/forgot-password">Forgot password?</Link>
          </div>
          <button
            type="submit"
            className={styles.primaryButton}
            disabled={loading}
          >
            {loading ? 'Logging in...' : 'Log In'}
          </button>
        </form>

        <div className={styles.authFooter}>
          Don't have an account? <Link to="/signup">Sign up</Link>
        </div>
      </div>
    </div>
  );
};

export default Login;