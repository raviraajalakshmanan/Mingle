import Alert from "@mui/material/Alert";
import Button from "@mui/material/Button";
import Divider from "@mui/material/Divider";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { getResults, type ResultOut } from "../lib/api";
import { formatSlot } from "../lib/format";

export default function Result() {
  const { token } = useParams<{ token: string }>();
  const [result, setResult] = useState<ResultOut | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!token) return;
    getResults(token)
      .then(setResult)
      .catch((e) => setError(e instanceof Error ? e.message : String(e)));
  }, [token]);

  if (error) {
    return (
      <Panel>
        <Typography variant="h2">Results not found</Typography>
        <Typography variant="subtitle1" sx={{ mt: 1 }}>
          This link may be invalid or the catch-up was removed.
        </Typography>
      </Panel>
    );
  }
  if (!result) {
    return (
      <Panel>
        <Typography variant="subtitle1">Loading…</Typography>
      </Panel>
    );
  }

  const shareUrl = window.location.href;
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(shareUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      setCopied(false);
    }
  };
  const whatsapp = `https://wa.me/?text=${encodeURIComponent(`Here's our plan: ${shareUrl}`)}`;

  // Empty state, no responses yet.
  if (!result.best_slot && result.alternatives.length === 0) {
    return (
      <Panel>
        <Typography variant="h1">The plan</Typography>
        <Typography variant="subtitle1" sx={{ mt: 1 }}>
          {result.message ?? "Waiting for responses."}
        </Typography>
        <Typography variant="subtitle1">{result.response_count} responded so far.</Typography>
      </Panel>
    );
  }

  // No-overlap state.
  if (!result.best_slot) {
    return (
      <Panel>
        <Typography variant="h1">Almost there</Typography>
        <Typography variant="subtitle1" sx={{ mt: 1, mb: 2 }}>
          {result.message}
        </Typography>
        <Stack spacing={1}>
          {result.alternatives.map((a) => (
            <Row
              key={a.id}
              left={a.label ?? formatSlot(a.starts_at, a.ends_at)}
              right={`${a.attending_headcount} people`}
            />
          ))}
        </Stack>
        <Responded responded={result.responded} />
      </Panel>
    );
  }

  const b = result.best_slot;
  const budget = result.budget!;

  return (
    <Panel>
      <Typography variant="h1" sx={{ mb: 3 }}>
        The plan
      </Typography>

      <Stack spacing={2.5}>
        <Block label="Best option" value={b.label ?? formatSlot(b.starts_at, b.ends_at)} />
        <Block label="Group" value={`${result.group_size} people`} />
        <Block
          label="Recommended budget"
          value={`₹${budget.per_person.low}–${budget.per_person.high} per person`}
          sub={
            `≈ ₹${budget.total.low}–${budget.total.high} total · ` +
            `works for ${Math.round(budget.inclusion_pct)}% comfortably` +
            (budget.contributions_total > 0
              ? ` · ₹${budget.contributions_total} pledged`
              : "")
          }
        />

        <div>
          <Typography variant="overline" sx={{ display: "block", mb: 1 }}>
            Suggestions
          </Typography>
          <Stack spacing={1.5}>
            {result.suggestions.map((s) => (
              <Paper
                key={s.title}
                variant="outlined"
                sx={{ p: 2, borderRadius: 3, borderColor: "divider" }}
              >
                <Stack
                  direction="row"
                  sx={{ justifyContent: "space-between", alignItems: "baseline" }}
                >
                  <Typography sx={{ fontWeight: 600 }}>{s.title}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    ₹{s.est_per_person.low}–{s.est_per_person.high} pp
                  </Typography>
                </Stack>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                  {s.blurb}
                </Typography>
              </Paper>
            ))}
          </Stack>
        </div>

        {result.rationale && (
          <Alert severity="info">
            {result.rationale}
          </Alert>
        )}

        {result.alternatives.length > 0 && (
          <div>
            <Typography variant="overline" sx={{ display: "block", mb: 1 }}>
              Other options
            </Typography>
            <Stack spacing={1}>
              {result.alternatives.map((a) => (
                <Row
                  key={a.id}
                  left={a.label ?? formatSlot(a.starts_at, a.ends_at)}
                  right={`${a.attending_headcount} people`}
                />
              ))}
            </Stack>
          </div>
        )}

        <Responded responded={result.responded} />

        <Divider />

        <Stack direction={{ xs: "column", sm: "row" }} spacing={1.5}>
          <Button variant="contained" onClick={copy} fullWidth>
            {copied ? "Copied" : "Copy result link"}
          </Button>
          <Button variant="outlined" href={whatsapp} target="_blank" rel="noreferrer" fullWidth>
            Share on WhatsApp
          </Button>
        </Stack>
      </Stack>
    </Panel>
  );
}

function Block({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div>
      <Typography variant="overline" sx={{ display: "block" }}>
        {label}
      </Typography>
      <Typography variant="h2">{value}</Typography>
      {sub && (
        <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
          {sub}
        </Typography>
      )}
    </div>
  );
}

function Row({ left, right }: { left: string; right: string }) {
  return (
    <Stack direction="row" sx={{ justifyContent: "space-between" }}>
      <Typography>{left}</Typography>
      <Typography color="text.secondary">{right}</Typography>
    </Stack>
  );
}

function Responded({ responded }: { responded: string[] }) {
  if (responded.length === 0) return null;
  return (
    <Typography variant="body2" color="text.secondary">
      Responded: {responded.join(", ")}
    </Typography>
  );
}

function Panel({ children }: { children: React.ReactNode }) {
  return (
    <Paper elevation={0} sx={{ p: { xs: 2.5, sm: 4 } }}>
      {children}
    </Paper>
  );
}
