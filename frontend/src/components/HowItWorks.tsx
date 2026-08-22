import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { brandGradient } from "../theme";

const STEPS = [
  {
    title: "Create & share",
    body: "Make a catch-up and send the link to friends on WhatsApp.",
  },
  {
    title: "Everyone answers privately",
    body: "Each person picks the times that suit them and a budget they're comfortable with. Nobody sees anyone else's.",
  },
  {
    title: "Get the best plan",
    body: "MigleUp finds the time that works for most people and an affordable plan for the whole group.",
  },
];

export default function HowItWorks() {
  return (
    <Stack spacing={2.5}>
      {STEPS.map((step, i) => (
        <Stack key={step.title} direction="row" spacing={2} sx={{ alignItems: "flex-start" }}>
          <Box
            sx={{
              flexShrink: 0,
              width: 30,
              height: 30,
              borderRadius: "50%",
              backgroundImage: brandGradient("action"),
              color: "#fff",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "0.9rem",
              fontWeight: 600,
              mt: "2px",
            }}
          >
            {i + 1}
          </Box>
          <div>
            <Typography sx={{ fontWeight: 600 }}>{step.title}</Typography>
            <Typography variant="body2" color="text.secondary">
              {step.body}
            </Typography>
          </div>
        </Stack>
      ))}
    </Stack>
  );
}
