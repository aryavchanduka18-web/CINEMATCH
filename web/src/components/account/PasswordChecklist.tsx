// Mirrors password_problem() in api/app/auth.py so people see the rules before they submit.
// The server decides; this only drives the live checklist.
export const PASSWORD_RULES: { label: string; ok: (pw: string) => boolean }[] = [
  { label: "8 or more characters", ok: (pw) => pw.length >= 8 },
  { label: "At least one letter and one number", ok: (pw) => /[A-Za-z]/.test(pw) && /\d/.test(pw) },
];

export function PasswordChecklist({ password }: { password: string }) {
  if (!password) return null;
  return (
    <ul className="space-y-1 text-xs" aria-label="Password rules">
      {PASSWORD_RULES.map((r) => {
        const ok = r.ok(password);
        return (
          <li key={r.label} className={ok ? "text-emerald-300" : "text-muted"}>
            <span aria-hidden>{ok ? "✓" : "○"}</span> {r.label}
            <span className="sr-only">{ok ? " (done)" : " (not yet)"}</span>
          </li>
        );
      })}
    </ul>
  );
}
