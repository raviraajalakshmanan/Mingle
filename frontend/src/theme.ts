import { createTheme } from "@mui/material/styles";

// Apple-inspired monochrome theme: white surfaces, near-black ink, soft grays,
// no blue. Restrained, elegant, mobile-first. Errors are shown as a refined
// rose-tinted panel rather than a loud red bar.
const INK = "#1d1d1f"; // Apple near-black
const GRAY = "#6e6e73"; // secondary text
const ERROR = "#b3261e";

const theme = createTheme({
  palette: {
    mode: "light",
    primary: { main: INK, contrastText: "#ffffff" },
    secondary: { main: GRAY },
    error: { main: ERROR },
    background: { default: "#f5f5f7", paper: "#ffffff" },
    text: { primary: INK, secondary: GRAY },
    divider: "rgba(0,0,0,0.08)",
  },
  shape: { borderRadius: 12 },
  typography: {
    fontFamily:
      '-apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro Display", "Segoe UI", Roboto, system-ui, sans-serif',
    h1: { fontSize: "1.9rem", fontWeight: 600, letterSpacing: "-0.02em", lineHeight: 1.15 },
    h2: { fontSize: "1.35rem", fontWeight: 600, letterSpacing: "-0.01em" },
    subtitle1: { color: GRAY, lineHeight: 1.5 },
    button: { textTransform: "none", fontWeight: 500 },
    overline: { letterSpacing: "0.08em", fontWeight: 600, color: GRAY },
  },
  components: {
    MuiButton: {
      defaultProps: { disableElevation: true },
      styleOverrides: {
        root: ({ ownerState }) => ({
          borderRadius: 980,
          padding: ownerState.size === "large" ? "13px 26px" : "10px 22px",
          fontSize: "1rem",
          ...(ownerState.variant === "contained" &&
            ownerState.color === "primary" && {
              backgroundColor: INK,
              "&:hover": { backgroundColor: "#000000" },
            }),
          ...(ownerState.variant === "outlined" &&
            ownerState.color === "primary" && {
              borderColor: "rgba(0,0,0,0.18)",
              color: INK,
              "&:hover": { borderColor: INK, backgroundColor: "rgba(0,0,0,0.03)" },
            }),
        }),
      },
    },
    MuiPaper: {
      styleOverrides: { rounded: { borderRadius: 20 } },
    },
    MuiTextField: {
      defaultProps: { variant: "outlined", fullWidth: true },
    },
    MuiOutlinedInput: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          backgroundColor: "#fff",
          "&.Mui-focused .MuiOutlinedInput-notchedOutline": { borderColor: INK },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: ({ ownerState }) => ({
          borderRadius: 980,
          fontWeight: 500,
          ...(ownerState.variant === "filled" &&
            ownerState.color === "primary" && { backgroundColor: INK }),
        }),
      },
    },
    MuiAlert: {
      defaultProps: { icon: false },
      styleOverrides: {
        root: ({ ownerState }) => ({
          borderRadius: 14,
          padding: "12px 16px",
          fontSize: "0.92rem",
          // Neutral, elegant informational panel (used for privacy notes).
          ...(ownerState.severity === "info" && {
            backgroundColor: "#f0f0f2",
            color: INK,
            border: "1px solid rgba(0,0,0,0.06)",
          }),
          // Beautiful error: soft rose panel, deep-red ink, subtle accent border.
          ...(ownerState.severity === "error" && {
            backgroundColor: "#fdeceb",
            color: ERROR,
            border: "1px solid rgba(179,38,30,0.18)",
            fontWeight: 500,
          }),
          ...(ownerState.severity === "success" && {
            backgroundColor: "#eef7f0",
            color: "#1d6b3a",
            border: "1px solid rgba(29,107,58,0.16)",
          }),
        }),
      },
    },
  },
});

export default theme;
