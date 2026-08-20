import CssBaseline from "@mui/material/CssBaseline";
import { ThemeProvider } from "@mui/material/styles";
import { LocalizationProvider } from "@mui/x-date-pickers/LocalizationProvider";
import { AdapterDayjs } from "@mui/x-date-pickers/AdapterDayjs";
import React from "react";
import ReactDOM from "react-dom/client";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import App from "./App";
import { AuthProvider } from "./lib/auth";
import Landing from "./routes/Landing";
import NewCatchup from "./routes/NewCatchup";
import Respond from "./routes/Respond";
import Result from "./routes/Result";
import theme from "./theme";
import "./styles.css";

// Route groups mirror docs/02-hld.md §2.1.
const router = createBrowserRouter([
  {
    element: <App />,
    children: [
      { path: "/", element: <Landing /> },
      { path: "/new", element: <NewCatchup /> }, // creator (auth)
      { path: "/r/:token", element: <Respond /> }, // responder (anon)
      { path: "/result/:token", element: <Result /> }, // shareable result
    ],
  },
]);

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <LocalizationProvider dateAdapter={AdapterDayjs}>
        <AuthProvider>
          <RouterProvider router={router} />
        </AuthProvider>
      </LocalizationProvider>
    </ThemeProvider>
  </React.StrictMode>
);
