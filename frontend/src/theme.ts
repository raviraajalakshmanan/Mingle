import { createTheme } from "@mui/material/styles";

// MigleUp theme. Apple-inspired monochrome foundation (white surfaces, near-black
// ink, soft grays) with the brand purple-to-teal gradient used as a deliberate,
// limited accent. Errors stay a refined rose panel, never a loud red bar.
//
// Colour roles are split by contrast, which is why there are two purples and two
// teals. The vivid pair is sampled straight from the logo and is decorative only.
// The deep pair is the one allowed under white text: raw teal #00ccb4 sits at
// 2.04:1 against white and would be unreadable on a button.
const INK = "#1d1d1f"; // Apple near-black, body copy and headings
const GRAY = "#6e6e73"; // secondary text
const ERROR = "#b3261e";

export const BRAND = {
  /** Vivid logo purple. Decorative surfaces only, never behind text. */
  purple: "#7824f0",
  /** Vivid logo teal. Decorative surfaces only, never behind text. */
  teal: "#00ccb4",
  /** Wordmark ink from the lockup. */
  navy: "#0a0a35",
  /** Gradient start under white text. 7.50:1, AAA. */
  actionFrom: "#6d1bd8",
  /** Gradient end under white text. 5.02:1, AA. */
  actionTo: "#0a7d70",
  /** Brand purple as text on white. 8.73:1, AAA. */
  accent: "#5f17c4",
} as const;

/** The brand gradient. Decorative by default, "action" for anything under text. */
export const brandGradient = (variant: "vivid" | "action" = "vivid") =>
  variant === "vivid"
    ? `linear-gradient(135deg, ${BRAND.purple} 0%, ${BRAND.teal} 100%)`
    : `linear-gradient(135deg, ${BRAND.actionFrom} 0%, ${BRAND.actionTo} 100%)`;

const ACTION_HOVER = "linear-gradient(135deg, #5f17c4 0%, #08655b 100%)";

const theme = createTheme({
  palette: {
    mode: "light",
    primary: { main: BRAND.actionFrom, contrastText: "#ffffff" },
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
          // Primary action carries the brand gradient. Secondary actions stay
          // neutral so a screen never shows two competing colour claims.
          ...(ownerState.variant === "contained" &&
            ownerState.color === "primary" && {
              backgroundImage: brandGradient("action"),
              backgroundColor: BRAND.actionFrom, // fallback if gradients are unsupported
              "&:hover": { backgroundImage: ACTION_HOVER },
              "&.Mui-disabled": {
                backgroundImage: "none",
                backgroundColor: "rgba(0,0,0,0.12)",
                color: "rgba(0,0,0,0.32)",
              },
            }),
          // Tertiary actions stay neutral so each screen makes one colour claim.
          ...(ownerState.variant === "text" &&
            ownerState.color === "primary" && {
              color: INK,
              "&:hover": { backgroundColor: "rgba(0,0,0,0.04)" },
            }),
          ...(ownerState.variant === "outlined" &&
            ownerState.color === "primary" && {
              borderColor: "rgba(0,0,0,0.18)",
              color: INK,
              "&:hover": { borderColor: INK, backgroundColor: "rgba(0,0,0,0.03)" },
            }),
          "&.Mui-focusVisible": {
            outline: `2px solid ${BRAND.accent}`,
            outlineOffset: 2,
          },
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
          "&.Mui-focused .MuiOutlinedInput-notchedOutline": {
            borderColor: BRAND.accent,
            borderWidth: 2,
          },
        },
      },
    },
    MuiInputLabel: {
      styleOverrides: { root: { "&.Mui-focused": { color: BRAND.accent } } },
    },
    MuiCheckbox: {
      styleOverrides: {
        root: { color: "rgba(0,0,0,0.32)", "&.Mui-checked": { color: BRAND.accent } },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: ({ ownerState }) => ({
          borderRadius: 980,
          fontWeight: 500,
          // A selected chip is a choice the person made, so it earns brand colour.
          ...(ownerState.variant === "filled" &&
            ownerState.color === "primary" && {
              backgroundImage: brandGradient("action"),
              backgroundColor: BRAND.actionFrom,
              color: "#fff",
              "&:hover": { backgroundImage: ACTION_HOVER },
            }),
          ...(ownerState.variant === "outlined" && {
            borderColor: "rgba(0,0,0,0.18)",
            color: INK,
          }),
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
          // Neutral, elegant informational panel (used for privacy notes). Kept
          // grey on purpose: the privacy promise should read as calm, not as a
          // marketing moment.
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
