import Box from "@mui/material/Box";
import Container from "@mui/material/Container";
import Link from "@mui/material/Link";
import Typography from "@mui/material/Typography";
import { Outlet } from "react-router-dom";

export default function App() {
  return (
    <Box
      sx={{
        minHeight: "100dvh",
        py: { xs: 3, sm: 6 },
        display: "flex",
        flexDirection: "column",
      }}
    >
      <Container maxWidth="sm" sx={{ flex: 1 }}>
        <Outlet />
      </Container>

      <Container maxWidth="sm">
        <Box
          component="footer"
          sx={{
            mt: { xs: 6, sm: 8 },
            pt: 2.5,
            borderTop: 1,
            borderColor: "divider",
          }}
        >
          <Typography variant="body2" color="text.secondary" sx={{ textAlign: "center" }}>
            Built by{" "}
            <Link
              href="https://raviraajalakshmanan.github.io/contact"
              target="_blank"
              rel="noreferrer"
              underline="hover"
              sx={{ color: "text.primary", fontWeight: 500 }}
            >
              RaviRaaja Lakshamanan
            </Link>
          </Typography>
        </Box>
      </Container>
    </Box>
  );
}
