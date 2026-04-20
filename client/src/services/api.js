import axios from 'axios';

const API_URL = "http://localhost:5000/api"; // Match Flask's port

// Create an Axios instance with a base URL
const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Attach Authorization header if token exists
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('token');
    if (token) {
        config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
});

// Global 401 handler: clear creds and redirect to login
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error?.response?.status === 401) {
            try {
                console.warn('401 Unauthorized – clearing session and redirecting to /login');
                localStorage.removeItem('token');
                localStorage.removeItem('user');
            } catch {}
            if (typeof window !== 'undefined' && window.location?.pathname !== '/login') {
                window.location.href = '/login';
            }
        }
        return Promise.reject(error);
    }
);

// Export the Axios instance
export default api;