import Box from "@mui/material/Box";
import markSrc from "../assets/logo-mark.png";
import lockupSrc from "../assets/logo-lockup.png";

/**
 * Brand marks. The artwork already carries the purple-to-teal gradient, so these
 * are the one place in the UI where the vivid brand colours appear at full
 * strength. Everything else uses the deeper action pair from `theme.ts`.
 */

/** Logomark on its own. Use for hero moments and tight spaces. */
export function LogoMark({ size = 64 }: { size?: number }) {
  return (
    <Box
      component="img"
      src={markSrc}
      alt=""
      aria-hidden
      sx={{ width: size, height: size, objectFit: "contain", display: "block" }}
    />
  );
}

/** Mark plus the MigleUp wordmark. Use in the header. */
export function LogoLockup({ height = 30 }: { height?: number }) {
  return (
    <Box
      component="img"
      src={lockupSrc}
      alt="MigleUp"
      sx={{ height, width: "auto", objectFit: "contain", display: "block" }}
    />
  );
}
