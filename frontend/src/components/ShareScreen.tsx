import Alert from "@mui/material/Alert";
import Button from "@mui/material/Button";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { closeCatchup, type CatchupCreated } from "../lib/api";

export default function ShareScreen({ created }: { created: CatchupCreated }) {
  const navigate = useNavigate();
  const [copied, setCopied] = useState(false);
  const [closing, setClosing] = useState(false);
  const [closed, setClosed] = useState(false);

  const message = `Let's plan a catch-up. Pick your times and a comfortable budget (private): ${created.invite_url}`;
  const whatsapp = `https://wa.me/?text=${encodeURIComponent(message)}`;

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(created.invite_url);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      setCopied(false);
    }
  };

  const onClose = async () => {
    setClosing(true);
    try {
      await closeCatchup(created.id);
      setClosed(true);
    } catch {
      /* leave open */
    } finally {
      setClosing(false);
    }
  };

  return (
    <Paper elevation={0} sx={{ p: { xs: 2.5, sm: 4 } }}>
      <Stack spacing={3}>
        <div>
          <Typography variant="h1">Your catch-up is ready</Typography>
          <Typography variant="subtitle1" sx={{ mt: 1 }}>
            Share this link. Everyone answers privately, and you only ever see the group's best
            option, never anyone's individual budget.
          </Typography>
        </div>

        <TextField
          label="Invite link"
          value={created.invite_url}
          slotProps={{ input: { readOnly: true } }}
          onFocus={(e) => e.target.select()}
        />

        <Stack direction={{ xs: "column", sm: "row" }} spacing={1.5}>
          <Button variant="contained" onClick={copy} fullWidth>
            {copied ? "Copied" : "Copy link"}
          </Button>
          <Button variant="outlined" href={whatsapp} target="_blank" rel="noreferrer" fullWidth>
            Share on WhatsApp
          </Button>
        </Stack>

        <Button variant="text" onClick={() => navigate(`/result/${created.result_token}`)}>
          See results
        </Button>

        {closed ? (
          <Alert severity="info">Responses closed, no new answers will be accepted.</Alert>
        ) : (
          <Button
            variant="text"
            color="inherit"
            onClick={onClose}
            disabled={closing}
            sx={{ color: "text.secondary" }}
          >
            {closing ? "Closing…" : "Close responses"}
          </Button>
        )}

        <Button variant="text" onClick={() => navigate("/new")} sx={{ color: "text.secondary" }}>
          Create another
        </Button>
      </Stack>
    </Paper>
  );
}
