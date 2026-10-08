import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { send } from "../api/client";

export function AuthPage({ mode }: { mode: "login" | "register" }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const qc = useQueryClient();
  const navigate = useNavigate();
  const go = useMutation({
    mutationFn: () => send("POST", `/auth/${mode}`, { email, password, display_name: name || undefined }),
    onSuccess: () => {
      qc.invalidateQueries();
      navigate("/");
    },
  });
  const field = "w-full rounded-md border border-white/15 bg-surface-2 px-3 py-2.5 text-sm focus:border-white/50 focus:outline-none";
  return (
    <div className="mx-auto max-w-sm px-4 pt-32">
      <h1 className="font-display text-3xl font-extrabold">{mode === "login" ? "Sign in" : "Create your account"}</h1>
      {mode === "register" && <p className="mt-2 text-sm text-muted">Everything you did as a guest is kept.</p>}
      <form className="mt-6 space-y-3" onSubmit={(e) => { e.preventDefault(); go.mutate(); }}>
        {mode === "register" && <input className={field} placeholder="Name (optional)" value={name} onChange={(e) => setName(e.target.value)} aria-label="Name" />}
        <input className={field} type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} required aria-label="Email" autoComplete="email" />
        <input className={field} type="password" placeholder="Password (8+ characters)" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={8} aria-label="Password"
          autoComplete={mode === "login" ? "current-password" : "new-password"} />
        {go.isError && <p className="text-sm text-red-300">{(go.error as Error).message}</p>}
        <button className="w-full rounded-md bg-white py-2.5 text-sm font-semibold text-black disabled:opacity-60" disabled={go.isPending}>
          {mode === "login" ? "Sign in" : "Create account"}
        </button>
      </form>
      <p className="mt-6 text-sm text-muted">
        {mode === "login" ? <>New here? <Link to="/register" className="text-white underline">Create an account</Link></> : <>Have an account? <Link to="/login" className="text-white underline">Sign in</Link></>}
      </p>
    </div>
  );
}