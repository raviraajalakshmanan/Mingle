import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Checkbox from "@mui/material/Checkbox";
import Chip from "@mui/material/Chip";
import Divider from "@mui/material/Divider";
import FormControlLabel from "@mui/material/FormControlLabel";
import FormGroup from "@mui/material/FormGroup";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { getInvite, submitResponse, type InviteSummary, type ResponseSubmit } from "../lib/api";
import { formatSlot } from "../lib/format";

const BUDGET_PRESETS = [
  { label: "Under ₹200", min: 0, max: 200 },
  { label: "₹200–500", min: 200, max: 500 },
  { label: "₹500–1000", min: 500, max: 1000 },
  { label: "₹1000–2000", min: 1000, max: 2000 },
  { label: "₹2000+", min: 2000, max: 5000 },
];

const INTERESTS = ["tea/coffee", "food", "walk", "park", "beach", "games", "sports", "day-trip"];

export default function Respond() {
  const { token } = useParams<{ token: string }>();

  const [invite, setInvite] = useState<InviteSummary | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [name, setName] = useState("");
  const [selectedSlots, setSelectedSlots] = useState<string[]>([]);
  const [companions, setCompanions] = useState(0);
  const [budgetIdx, setBudgetIdx] = useState<number | null>(null);
  const [contribution, setContribution] = useState("");
  const [interests, setInterests] = useState<string[]>([]);
  const [website, setWebsite] = useState(""); // honeypot

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  useEffect(() => {
    if (!token) return;
    getInvite(token)
      .then(setInvite)
      .catch((e) => setLoadError(e instanceof Error ? e.message : String(e)));
  }, [token]);

  if (loadError) {
    return (
      <Panel>
        <Typography variant="h2">Invite not found</Typography>
        <Typography variant="subtitle1" sx={{ mt: 1 }}>
          This link may be invalid or the catch-up was removed.
        </Typography>
      </Panel>
    );
  }

  if (!invite) {
    return (
      <Panel>
        <Typography variant="subtitle1">Loading…</Typography>
      </Panel>
    );
  }

  if (done) {
    return (
      <Panel>
        <Typography variant="h1">Thanks, you're in</Typography>
        <Typography variant="subtitle1" sx={{ mt: 1.5 }}>
          Your budget and availability stay private. The organiser only sees the group's best
          option, never your individual answers.
        </Typography>
      </Panel>
    );
  }

  const toggle = (list: string[], value: string) =>
    list.includes(value) ? list.filter((v) => v !== value) : [...list, value];

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (selectedSlots.length === 0) {
      setError("Pick at least one time that works for you.");
      return;
    }
    if (budgetIdx === null) {
      setError("Choose a comfortable spending range.");
      return;
    }
    const preset = BUDGET_PRESETS[budgetIdx];
    const body: ResponseSubmit = {
      name: name.trim(),
      slot_ids: selectedSlots,
      companions,
      budget_min: preset.min,
      budget_max: preset.max,
      contribution: contribution ? Math.max(0, parseInt(contribution, 10) || 0) : 0,
      interests,
      website,
    };

    setSubmitting(true);
    try {
      await submitResponse(token!, body);
      try {
        localStorage.setItem(`migleup:responded:${token}`, "1");
      } catch {
        /* ignore */
      }
      setDone(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSubmitting(false);
    }
  };

  const subtitleParts = [
    invite.creator_first_name ? `${invite.creator_first_name} invited you` : null,
    invite.location || null,
  ].filter(Boolean);

  return (
    <Panel>
      <Typography variant="h1">{invite.title}</Typography>
      {subtitleParts.length > 0 && (
        <Typography variant="subtitle1" sx={{ mt: 0.5 }}>
          {subtitleParts.join(" · ")}
        </Typography>
      )}
      {invite.message && (
        <Typography sx={{ mt: 1.5 }}>{invite.message}</Typography>
      )}

      <Alert severity="info" sx={{ mt: 2 }}>
        Your budget and availability stay private. Nobody else can see them.
      </Alert>

      <Box component="form" onSubmit={onSubmit} sx={{ mt: 3 }}>
        <Stack spacing={3}>
          <TextField
            label="Your name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            slotProps={{ htmlInput: { maxLength: 80 } }}
          />

          {/* Honeypot, hidden from real users. */}
          <input
            type="text"
            name="website"
            className="hp-field"
            tabIndex={-1}
            autoComplete="off"
            aria-hidden="true"
            value={website}
            onChange={(e) => setWebsite(e.target.value)}
          />

          <Field label="Which times work for you?">
            <FormGroup>
              {invite.slots.map((s) => (
                <FormControlLabel
                  key={s.id}
                  control={
                    <Checkbox
                      checked={selectedSlots.includes(s.id)}
                      onChange={() => setSelectedSlots((cur) => toggle(cur, s.id))}
                    />
                  }
                  label={s.label ?? formatSlot(s.starts_at, s.ends_at)}
                />
              ))}
            </FormGroup>
          </Field>

          <TextField
            label="How many people are you bringing?"
            type="number"
            value={companions}
            onChange={(e) => setCompanions(Math.max(0, parseInt(e.target.value, 10) || 0))}
            slotProps={{ htmlInput: { min: 0, max: 50 } }}
          />

          <Field label="Comfortable spending (per person)">
            <Stack direction="row" sx={{ flexWrap: "wrap", gap: 1 }}>
              {BUDGET_PRESETS.map((p, i) => (
                <Chip
                  key={p.label}
                  label={p.label}
                  onClick={() => setBudgetIdx(i)}
                  color={budgetIdx === i ? "primary" : "default"}
                  variant={budgetIdx === i ? "filled" : "outlined"}
                />
              ))}
            </Stack>
          </Field>

          <TextField
            label="Chip in extra toward shared costs (optional, ₹)"
            type="number"
            value={contribution}
            onChange={(e) => setContribution(e.target.value)}
            placeholder="0"
            slotProps={{ htmlInput: { min: 0 } }}
          />

          <Field label="What are you up for? (optional)">
            <Stack direction="row" sx={{ flexWrap: "wrap", gap: 1 }}>
              {INTERESTS.map((it) => (
                <Chip
                  key={it}
                  label={it}
                  onClick={() => setInterests((cur) => toggle(cur, it))}
                  color={interests.includes(it) ? "primary" : "default"}
                  variant={interests.includes(it) ? "filled" : "outlined"}
                />
              ))}
            </Stack>
          </Field>

          {error && <Alert severity="error">{error}</Alert>}

          <Button variant="contained" size="large" type="submit" disabled={submitting}>
            {submitting ? "Sending…" : "Send my private response"}
          </Button>
        </Stack>
      </Box>
    </Panel>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <Divider textAlign="left" sx={{ mb: 1.5 }}>
        <Typography variant="overline">{label}</Typography>
      </Divider>
      {children}
    </div>
  );
}

function Panel({ children }: { children: React.ReactNode }) {
  return (
    <Paper elevation={0} sx={{ p: { xs: 2.5, sm: 4 } }}>
      {children}
    </Paper>
  );
}
