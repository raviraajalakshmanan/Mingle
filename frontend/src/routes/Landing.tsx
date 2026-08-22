import Alert from "@mui/material/Alert";
import Button from "@mui/material/Button";
import Divider from "@mui/material/Divider";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { useNavigate } from "react-router-dom";
import HowItWorks from "../components/HowItWorks";

export default function Landing() {
  const navigate = useNavigate();

  return (
    <Paper elevation={0} sx={{ p: { xs: 3, sm: 5 } }}>
      <Stack spacing={4}>
        <Stack spacing={2} sx={{ textAlign: "center", alignItems: "center" }}>
          <Typography variant="h1">Meet up, minus the money talk.</Typography>
          <Typography variant="subtitle1" sx={{ maxWidth: 440 }}>
            MigleUp helps friends plan a get-together where everyone's budget stays private, so
            nobody feels priced out.
          </Typography>
          <Button variant="contained" size="large" onClick={() => navigate("/new")}>
            Create a catch-up
          </Button>
        </Stack>

        <Divider />

        <Typography variant="overline" sx={{ display: "block", textAlign: "center" }}>
          How it works
        </Typography>
        <HowItWorks />

        <Alert severity="info">
          Private by design. No one, not even the organiser, ever sees an individual's budget or
          availability. You only see the group's best option.
        </Alert>
      </Stack>
    </Paper>
  );
}
