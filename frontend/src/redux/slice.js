import { createSlice } from '@reduxjs/toolkit'

const initialState = {
    username: "",
    measures: [],
    permissions: 0,
    buttonState: false,
    pumpBroken: false,
    isBlocked: false

}

export const userSlice = createSlice({
    name: 'user',
    initialState,
    reducers: {
        setUser(store, action) {
            store.username = action.payload.login
            store.permissions = action.payload.permissions
            store.isBlocked = action.payload.is_blocked
            store.pumpBroken = action.payload.pump_broken
            store.buttonState = action.payload.button_state
        },

        setMeasures(store, action) {
            const data = action.payload
            store.measures = data.slice(Math.max(0, data.length-100))
        },

        setButtonState(store, action) {
            store.buttonState = action.payload
        }
    },
})

export const { setUser, setMeasures, setButtonState } = userSlice.actions

export default userSlice.reducer