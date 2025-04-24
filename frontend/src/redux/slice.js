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
        },

        setMeasures(store, action) {
            const data = action.payload
            store.measures = data.slice(Math.max(0, data.length-100))
        },

        setButtonState(store, action) {
            store.buttonState = action.payload
        },

        setIsBlocked(store, action) {
            store.isBlocked = action.payload
        },

        setPumpIsBroken(store, action) {
            store.pumpBroken = action.payload
        }
    },
})

export const { setUser, setMeasures, setButtonState, setIsBlocked, setPumpIsBroken } = userSlice.actions

export default userSlice.reducer