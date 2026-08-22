import Box from "@mui/material/Box";
import Container from "@mui/material/Container";
import Link from "@mui/material/Link";
import Typography from "@mui/material/Typography";
import { Link as RouterLink, Outlet } from "react-router-dom";
import { LogoLockup } from "./components/Logo";

export default function App() {
  return (
    <Box
      sx={{
        minHeight: "100dvh",
        py: { xs: 2.5, sm: 4 },
        display: "flex",
        flexDirection: "column",
      }}
    >
      <Container maxWidth="sm">
        <Box
          component="header"
          sx={{ display: "flex", justifyContent: "center", mb: { xs: 3, sm: 4 } }}
        >
          <RouterLink
            to="/"
            aria-label="MigleUp home"
            style={{ display: "inline-flex", textDecoration: "none" }}
          >
            <LogoLockup height={30} />
          </RouterLink>
        </Box>
      </Container>

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
