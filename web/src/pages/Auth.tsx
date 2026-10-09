import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ApiError, send } from "../api/client";
import { useMe } from "../api/hooks";
import { PasswordChecklist } from "../components/account/PasswordChecklist";

export const field = "w-full rounded-md border border-white/15 bg-surface-2 px-3 py-2.5 text-sm focus:border-white/50 focus:outline-none";

/** The server's own sentence, with a friendlier fallback when the network itself failed. */
export function errorText(e: unknown): string {
  if (e instanceof ApiError) return e.message;
  return "Could not reach CineMatch. Check your connection and try again.";
}

export function AuthPage({ mode }: { mode: "login" | "register" }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const { data: me } = useMe();
  const qc = useQueryClient();
  const navigate = useNavigate();
  const go = useMutation({
    mutationFn: () => send("POST", `/auth/${mode}`, { email, password, display_name: name || undefined }),
    onSuccess: () => {
      qc.invalidateQueries();
      navigate("/");
    },
  });
  const keeps = mode === "register" && me?.is_guest && (Number(me.counts.ratings) > 0 || Number(me.counts.likes) > 0 || Number(me.counts.list) > 0);
  return (
    <div className="mx-auto max-w-sm px-4 pt-32">
      <h1 className="font-display text-3xl font-extrabold">{mode === "login" ? "Sign in" : "Create your account"}</h1>
      {mode === "register" && (
        <p className="mt-2 text-sm text-muted">
          {keeps ? "Your ratings, likes and My List from this guest session move into the new account." : "Your ratings, likes and list stay with you on any device."}
        </p>
      )}
      <form className="mt-6 space-y-3" onSubmit={(e) => { e.preventDefault(); go.mutate(); }} noValidate>
        {mode === "register" && <input className={field} placeholder="Name (optional)" value={name} onChange={(e) => setName(e.target.value)} aria-label="Name" maxLength={80} />}
        <input className={field} type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} required aria-label="Email" autoComplete="email" />
        <input className={field} type="password" placeholder={mode === "register" ? "Password (8+ characters, a letter and a number)" : "Password"}
          value={password} onChange={(e) => setPassword(e.target.value)} required aria-label="Password"
          autoComplete={mode === "login" ? "current-password" : "new-password"} />
        {mode === "register" && <PasswordChecklist password={password} />}
        {go.isError && <p role="alert" className="rounded-md bg-red-500/10 px-3 py-2 text-sm text-red-300">{errorText(go.error)}</p>}
        <button className="w-full rounded-md bg-white py-2.5 text-sm font-semibold text-black disabled:opacity-60" disabled={go.isPending || !email || !password}>
          {go.isPending ? "One moment..." : mode === "login" ? "Sign in" : "Create account"}
        </button>
      </form>
      <p className="mt-6 text-sm text-muted">
        {mode === "login" ? <>New here? <Link to="/register" className="text-white underline">Create an account</Link></> : <>Have an account? <Link to="/login" className="text-white underline">Sign in</Link></>}
      </p>
      {mode === "login" && (
        <p className="mt-3 text-xs text-muted">Forgot your password? CineMatch has no email service yet, so passwords cannot be reset by email.</p>
      )}
    </div>
  );
}
