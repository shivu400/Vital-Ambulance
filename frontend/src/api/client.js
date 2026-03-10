import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const predict = async (vitalData) => {
  try {
    const response = await client.post('/v1/predict', vitalData)
    return response.data
  } catch (error) {
    console.error('Prediction error:', error)
    throw error
  }
}

export const healthCheck = async () => {
  try {
    const response = await client.get('/health')
    return response.data
  } catch (error) {
    console.error('Health check error:', error)
    throw error
  }
}

export default client
