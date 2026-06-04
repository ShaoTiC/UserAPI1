import axios from 'axios'

const http = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

const unwrap = (response) => response.data.data

export const resumeApi = {
  stats: () => http.get('/resumes/stats').then(unwrap),
  list: (params) => http.get('/resumes', { params }).then(unwrap),
  detail: (id) => http.get(`/resumes/${id}`).then(unwrap),
  updateStatus: (id, status) => http.patch(`/resumes/${id}/status`, { status }).then(unwrap),
}

export const chatBotApi = {
  list: (params) => http.get('/chatbots', { params }).then(unwrap),
  updateStatus: (id, status) => http.patch(`/chatbots/${id}/status`, { status }).then(unwrap),
}
