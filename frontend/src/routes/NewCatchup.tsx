import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Divider from "@mui/material/Divider";
import MenuItem from "@mui/material/MenuItem";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import { MobileDateTimePicker } from "@mui/x-date-pickers/MobileDateTimePicker";
import dayjs, { type Dayjs } from "dayjs";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import HowItWorks from "../components/HowItWorks";
import ShareScreen from "../components/ShareScreen";
import { createCatchup, type CatchupCreated, type CatchupType, type SlotIn } from "../lib/api";
import { useAuth } from "../lib/auth";
import { DATE_TIME_FORMAT } from "../lib/format";

const TYPES: { value: CatchupType; label: string }[] = [
  { value: "casual", label: "Casual catch-up" },
  { value: "food", label: "Food" },
  { value: "activity", label: "Activity" },
  { value: "outing", label: "Outing" },
  { value: "trip", label: "Trip" },
];

interface SlotRow {
  start: Dayjs | null;
  end: Dayjs | null;
}

/**
 * Now, rounded up to the next quarter hour. Prefilled times use this so a form
 * left open for a minute does not start out already in the past.
 */
function nextQuarterHour(): Dayjs {
  const now = dayjs().second(0).millisecond(0);
  const over = now.minute() % 15;
  return over === 0 ? now : now.add(15 - over, "minute");
}

/** A time option prefilled from `start`, running two hours. */
function defaultSlot(start: Dayjs = nextQuarterHour()): SlotRow {
  return { start, end: start.add(2, "hour") };
}

export default function NewCatchup() {
  const { session, loading, configured, signInWithGoogle, signOut } = useAuth();
  const navigate = useNavigate();

  const [title, setTitle] = useState("");
  const [type, setType] = useState<CatchupType>("casual");
  const [location, setLocation] = useState("");
  const [message, setMessage] = useState("");
  const [deadline, setDeadline] = useState<Dayjs | null>(null);
  const [maxResponses, setMaxResponses] = useState("");
  const [slots, setSlots] = useState<SlotRow[]>(() => [defaultSlot()]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [created, setCreated] = useState<CatchupCreated | null>(null);

  if (!configured) {
    return (
      <Panel>
        <Typography variant="h2">Not configured</Typography>
        <Typography variant="subtitle1">
          Set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY to sign in.
        </Typography>
      </Panel>
    );
  }

  if (loading) {
    return (
      <Panel>
        <Typography variant="subtitle1">Loading…</Typography>
      </Panel>
    );
  }

  if (!session) {
    return (
      <Panel>
        <Stack spacing={3}>
          <div>
            <Typography variant="h1">Meet up, minus the money talk.</Typography>
            <Typography variant="subtitle1" sx={{ mt: 1 }}>
              MigleUp finds a time and an affordable plan that works for your whole group, while
              keeping everyone's budget private.
            </Typography>
          </div>

          <Divider textAlign="left">
            <Typography variant="overline">How it works</Typography>
          </Divider>
          <HowItWorks />

          <Divider />

          <Stack spacing={1}>
            <Typography variant="body2" color="text.secondary">
              Sign in to create a catch-up and get a shareable link. Friends you invite don't need
              an account.
            </Typography>
            <Button variant="contained" size="large" onClick={signInWithGoogle}>
              Continue with Google
            </Button>
            <Button variant="text" onClick={() => navigate("/")} sx={{ alignSelf: "flex-start" }}>
              Back
            </Button>
          </Stack>
        </Stack>
      </Panel>
    );
  }

  if (created) return <ShareScreen created={created} />;

  // Nothing may be scheduled before this. Read fresh on every render so the
  // bound keeps moving while the form sits open.
  const earliest = dayjs();

  const updateSlot = (i: number, patch: Partial<SlotRow>) =>
    setSlots((rows) => rows.map((r, idx) => (idx === i ? { ...r, ...patch } : r)));
  // Another option most often means the same time on another day.
  const addSlot = () =>
    setSlots((rows) => {
      const prev = rows[rows.length - 1]?.start;
      const next = nextQuarterHour();
      const start = prev?.add(1, "day") ?? next;
      return [...rows, defaultSlot(start.isBefore(next) ? next : start)];
    });
  const removeSlot = (i: number) =>
    setSlots((rows) => (rows.length > 1 ? rows.filter((_, idx) => idx !== i) : rows));

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const cleaned: SlotIn[] = [];
    for (const s of slots) {
      if (!s.start || !s.end) {
        setError("Every time option needs a start and end.");
        return;
      }
      if (!s.end.isAfter(s.start)) {
        setError("Each option's end time must be after its start time.");
        return;
      }
      if (s.start.isBefore(dayjs())) {
        setError("Time options have to be in the future.");
        return;
      }
      cleaned.push({ starts_at: s.start.toISOString(), ends_at: s.end.toISOString() });
    }

    if (deadline && deadline.isBefore(dayjs())) {
      setError("The response deadline has to be in the future.");
      return;
    }

    setSubmitting(true);
    try {
      const maxResp = maxResponses ? Math.max(1, parseInt(maxResponses, 10) || 0) : undefined;
      const result = await createCatchup({
        title: title.trim(),
        type,
        location: location.trim() || undefined,
        message: message.trim() || undefined,
        deadline: deadline ? deadline.toISOString() : undefined,
        max_responses: maxResp,
        slots: cleaned,
      });
      setCreated(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Panel>
      <Stack
        direction="row"
        sx={{ justifyContent: "space-between", alignItems: "center", mb: 3 }}
      >
        <Typography variant="h1">Create a catch-up</Typography>
        <Button variant="text" size="small" onClick={signOut}>
          Sign out
        </Button>
      </Stack>

      <Box component="form" onSubmit={onSubmit}>
        <Stack spacing={2.5}>
          <TextField
            label="Title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Let's meet this Saturday evening"
            required
            slotProps={{ htmlInput: { maxLength: 200 } }}
          />

          <TextField
            select
            label="Type"
            value={type}
            onChange={(e) => setType(e.target.value as CatchupType)}
          >
            {TYPES.map((t) => (
              <MenuItem key={t.value} value={t.value}>
                {t.label}
              </MenuItem>
            ))}
          </TextField>

          <TextField
            label="Approximate location"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            placeholder="Indiranagar"
          />

          <TextField
            label="Message (optional)"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            multiline
            minRows={2}
          />

          <Divider textAlign="left">
            <Typography variant="overline">Time options</Typography>
          </Divider>

          {slots.map((s, i) => (
            <Stack key={i} spacing={1.5} sx={{ pb: 1 }}>
              <Typography variant="overline" sx={{ display: "block" }}>
                Option {i + 1}
              </Typography>
              <MobileDateTimePicker
                label="Starts"
                format={DATE_TIME_FORMAT}
                minDateTime={earliest}
                value={s.start}
                onChange={(v) => updateSlot(i, { start: v })}
                slotProps={{ textField: { fullWidth: true } }}
              />
              <MobileDateTimePicker
                label="Ends"
                format={DATE_TIME_FORMAT}
                minDateTime={s.start ?? earliest}
                value={s.end}
                onChange={(v) => updateSlot(i, { end: v })}
                slotProps={{ textField: { fullWidth: true } }}
              />
              {slots.length > 1 && (
                <Button
                  variant="text"
                  size="small"
                  color="inherit"
                  onClick={() => removeSlot(i)}
                  sx={{ alignSelf: "flex-start", color: "text.secondary" }}
                >
                  Remove option
                </Button>
              )}
            </Stack>
          ))}

          <Button variant="text" onClick={addSlot} sx={{ alignSelf: "flex-start" }}>
            Add another time
          </Button>

          <Divider />

          <MobileDateTimePicker
            label="Response deadline (optional)"
            format={DATE_TIME_FORMAT}
            minDateTime={earliest}
            value={deadline}
            onChange={setDeadline}
            slotProps={{
              textField: { fullWidth: true },
              actionBar: { actions: ["clear", "accept"] },
            }}
          />

          <TextField
            label="Limit number of responses (optional)"
            type="number"
            value={maxResponses}
            onChange={(e) => setMaxResponses(e.target.value)}
            placeholder="e.g. 15"
            slotProps={{ htmlInput: { min: 1 } }}
          />

          {error && <Alert severity="error">{error}</Alert>}

          <Button variant="contained" size="large" type="submit" disabled={submitting}>
            {submitting ? "Creating…" : "Create & get link"}
          </Button>
        </Stack>
      </Box>
    </Panel>
  );
}

function Panel({ children }: { children: React.ReactNode }) {
  return (
    <Paper elevation={0} sx={{ p: { xs: 2.5, sm: 4 } }}>
      {children}
    </Paper>
  );
}
