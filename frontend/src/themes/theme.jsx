import { createTheme } from "@mui/material/styles";

const theme = createTheme({
    palette: {
      primary: {
        main: '#ffffff',
      },
      text: {
        primary: '#ffffff',
        secondary: '#cccccc',
      },
      background: {
        paper: '#222'
      }
    },
    components: {
      MuiDivider: {
        styleOverrides: {
          root: {
            borderColor: '#ffffff',
            borderWidth: '2px',
          },
        },
      },
      MuiOutlinedInput: {
        styleOverrides: {
          notchedOutline: {
            borderColor: '#ffffff',
            borderWidth: '2px',
          },
        },
      },
      MuiButton: {
        styleOverrides: {
          root: {
            color: '#ffffff',
          },
        },
      },
      MuiInput: {
        styleOverrides: {
          root: {
            border: '2px solid #7db0f3',
            borderRadius: '5px',
          },
          notchedOutline: {
            border: 'none',
          },
        },
      },
    },
  });

  export default theme