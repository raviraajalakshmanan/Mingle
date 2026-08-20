import Box from "@mui/material/Box";
import Container from "@mui/material/Container";
import { Outlet } from "react-router-dom";

export default function App() {
  return (
    <Box sx={{ minHeight: "100dvh", py: { xs: 3, sm: 6 } }}>
      <Container maxWidth="sm">
        <Outlet />
      </Container>
    </Box>
  );
}
