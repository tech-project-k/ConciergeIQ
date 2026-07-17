import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8085/api',
});

// Automatically inject JWT authentication headers
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export default api;
