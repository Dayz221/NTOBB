import { configureStore } from "@reduxjs/toolkit"
import userReducer from "./slice.js"

export const store = configureStore({
    reducer: {
        user: userReducer 
    },
})
