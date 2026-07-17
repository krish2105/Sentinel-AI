"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "motion/react";
import { Copy, KeyRound, LogIn, ShieldCheck, UserPlus } from "lucide-react";
import { useAuth } from "@/components/AuthProvider";
import { useToast } from "@/components/Toaster";

type Tab = "signin" | "register";

export default function AuthPage() {
  const { loginWithApiKey, register } = useAuth();
  const { toast } = useToast();
  const router = useRouter();
  const [tab, setTab] = useState<Tab>("signin");
  const [email, setEmail] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [issuedKey, setIssuedKey] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const doRegister = async () => {
    if (!email.trim()) return toast("Enter an email to register.", "error");
    setBusy(true);
    try {
      const { api_key } = await register(email.trim());
      setIssuedKey(api_key);
      setApiKey(api_key);
      toast("API key created — copy it now, it is shown only once.", "success");
    } catch (e) {
      toast(e instanceof Error ? e.message : "Registration failed.", "error");
    }
    setBusy(false);
  };

  const doSignin = async () => {
    if (!apiKey.trim()) return toast("Paste your API key to sign in.", "error");
    setBusy(true);
    try {
      await loginWithApiKey(apiKey.trim(), email.trim() || undefined);
      toast("Signed in.", "success");
      router.push("/targets");
    } catch (e) {
      toast(e instanceof Error ? e.message : "Sign in failed.", "error");
    }
    setBusy(false);
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-6 pt-24 pb-16">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
        className="w-full max-w-md"
      >
        <div className="flex items-center gap-2 mb-6 justify-center">
          <span className="relative flex h-9 w-9 items-center justify-center rounded-xl bg-cyan/10">
            <ShieldCheck className="h-5 w-5 text-cyan" />
          </span>
          <span className="font-semibold text-lg tracking-tight">
            Sentinel<span className="text-cyan">AI</span>
          </span>
        </div>

        <div className="glass rounded-2xl p-6">
          {/* Tabs */}
          <div className="flex gap-1 p-1 rounded-xl bg-base/50 mb-6">
            {(["signin", "register"] as Tab[]).map((t) => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={
                  "flex-1 py-2 rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-1.5 " +
                  (tab === t ? "bg-cyan/15 text-cyan" : "text-muted hover:text-fg")
                }
              >
                {t === "signin" ? (
                  <>
                    <LogIn className="h-4 w-4" /> Sign in
                  </>
                ) : (
                  <>
                    <UserPlus className="h-4 w-4" /> Register
                  </>
                )}
              </button>
            ))}
          </div>

          {tab === "register" ? (
            <div className="space-y-4">
              <p className="text-sm text-muted">
                Register to get a personal API key. Your targets, runs, and reports
                are scoped to your account.
              </p>
              <Field label="Email">
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@company.com"
                  className="auth-input"
                />
              </Field>
              {issuedKey && (
                <div className="rounded-xl border border-cyan/40 bg-cyan/5 p-3">
                  <div className="flex items-center gap-1.5 text-xs text-cyan mb-1.5">
                    <KeyRound className="h-3.5 w-3.5" /> Your API key (shown once)
                  </div>
                  <div className="flex items-center gap-2">
                    <code className="mono text-[11px] break-all flex-1 text-fg">
                      {issuedKey}
                    </code>
                    <button
                      onClick={() => {
                        navigator.clipboard?.writeText(issuedKey);
                        toast("Copied to clipboard.", "success");
                      }}
                      aria-label="Copy API key"
                      className="text-muted hover:text-cyan transition-colors"
                    >
                      <Copy className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              )}
              <button
                onClick={issuedKey ? doSignin : doRegister}
                disabled={busy}
                className="w-full rounded-xl bg-cyan text-accent-fg font-medium py-2.5 hover:shadow-glow transition-shadow disabled:opacity-50"
              >
                {busy ? "Working…" : issuedKey ? "Continue → sign in" : "Create API key"}
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              <p className="text-sm text-muted">
                Paste the API key you received at registration.
              </p>
              <Field label="API key">
                <input
                  type="password"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="snt_…"
                  className="auth-input mono"
                />
              </Field>
              <button
                onClick={doSignin}
                disabled={busy}
                className="w-full rounded-xl bg-cyan text-accent-fg font-medium py-2.5 hover:shadow-glow transition-shadow disabled:opacity-50"
              >
                {busy ? "Signing in…" : "Sign in"}
              </button>
            </div>
          )}

          <p className="text-[11px] text-muted mt-5 text-center leading-relaxed">
            No account?{" "}
            <span className="text-cyan">You can still explore in demo mode</span> —
            everything works without signing in, scoped to a shared demo user.
          </p>
        </div>
      </motion.div>

      <style jsx global>{`
        .auth-input {
          width: 100%;
          background: rgb(var(--c-base));
          border: 1px solid rgb(var(--c-line));
          border-radius: 0.6rem;
          padding: 0.6rem 0.8rem;
          font-size: 0.9rem;
          color: rgb(var(--c-fg));
          transition: border-color 0.2s;
        }
        .auth-input:focus {
          border-color: rgb(var(--c-cyan));
          outline: none;
        }
      `}</style>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="block text-xs text-muted mb-1.5">{label}</label>
      {children}
    </div>
  );
}
