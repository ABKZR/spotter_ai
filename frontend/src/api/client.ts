import axios from 'axios';

const client = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30_000,
});

client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (axios.isAxiosError(error) && error.response?.data?.error) {
      const apiError = error.response.data.error;
      const err = new Error(apiError.message || 'An unexpected error occurred');
      (err as Error & { code: string }).code = apiError.code;
      return Promise.reject(err);
    }
    return Promise.reject(error);
  }
);

export default client;
