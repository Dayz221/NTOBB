import axios from "axios"

const API = axios.create({
    baseURL: "http://localhost:5000"
})

API.interceptors.request.use((state) => {
    const token = localStorage.getItem("token")
    state.headers.Authorization = `Bearer ${token}`
    return state
})

export default API