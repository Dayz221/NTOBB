import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import './styles/colors.css'
import './styles/index.css'
import './styles/reset.css'
import UserPage from './pages/user/userPage'
import AdminPage from './pages/admin/adminPage'
import LoginPage from './pages/login/loginPage'
import RegisterPage from './pages/register/registerPage'
import { store } from './redux/store.js'
import { Provider } from 'react-redux'
import { ThemeProvider } from '@mui/material/styles'
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import theme from './themes/theme.jsx'
import UserPageFromAdmin from './pages/user_from_admin/userPageFromAdmin.jsx'

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <BrowserRouter>
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <ThemeProvider theme={theme}>
        <Provider store={store}>
          <Routes>
            <Route path="/" element={<UserPage />} />
            <Route path="/admin" element={<AdminPage />} />
            <Route path="/user/:id" element={<UserPageFromAdmin />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
          </Routes>
        </Provider>
      </ThemeProvider>
    </LocalizationProvider>
  </BrowserRouter>
);