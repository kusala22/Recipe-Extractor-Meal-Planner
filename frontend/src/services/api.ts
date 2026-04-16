import axios from 'axios'

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

export const api = axios.create({
  baseURL: API_BASE_URL,
})

export const extractRecipe = async (url: string) => {
  const response = await api.post('/extract', { url })
  return response.data
}

export const getSavedRecipes = async () => {
  const response = await api.get('/recipes')
  return response.data
}

export const getRecipeDetails = async (id: number) => {
  const response = await api.get(`/recipes/${id}`)
  return response.data
}
