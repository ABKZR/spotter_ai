import axios from 'axios';

function getApiBaseUrl(): string {
  const envUrl = import.meta.env.VITE_API_BASE_URL?.trim();
  if (!envUrl) {
    return '/api/v1';
  }
  let normalized = envUrl;
  if (!normalized.startsWith('http://') && !normalized.startsWith('https://')) {
    normalized = `https://${normalized}`;
  }
  normalized = normalized.replace(/\/+$/, '');
  if (!normalized.endsWith('/api/v1')) {
    normalized = `${normalized}/api/v1`;
  }
  return normalized;
}

const client = axios.create({
  baseURL: getApiBaseUrl(),
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
