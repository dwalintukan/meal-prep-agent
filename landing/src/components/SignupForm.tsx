import { useState } from "react";
import { Check, ArrowRight } from "lucide-react";

// ─────────────────────────────────────────────────────────────
// CONFIG — point PUBLIC_SIGNUP_ENDPOINT at your email service
// (Mailchimp, ConvertKit, Resend, Formspree, or your own API).
// The form POSTs JSON: { "email": "user@example.com" }
// ─────────────────────────────────────────────────────────────
const SIGNUP_ENDPOINT =
  import.meta.env.PUBLIC_SIGNUP_ENDPOINT ?? "https://your-api.example.com/signup";

type Status = "idle" | "loading" | "success" | "error";

interface Props {
  id: string;
  dark?: boolean;
}

export default function SignupForm({ id, dark = false }: Props) {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<Status>("idle");

  const submit = async () => {
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setStatus("error");
      return;
    }
    setStatus("loading");
    try {
      const res = await fetch(SIGNUP_ENDPOINT, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      setStatus(res.ok ? "success" : "error");
    } catch {
      setStatus("error");
    }
  };

  if (status === "success") {
    return (
      <div
        className={`flex items-center gap-2 rounded-xl px-5 py-4 font-medium ${
          dark ? "bg-emerald-500/20 text-emerald-200" : "bg-emerald-100 text-emerald-800"
        }`}
      >
        <Check className="h-5 w-5 shrink-0" />
        You're on the list! We'll email you when your invite is ready.
      </div>
    );
  }

  return (
    <div className="w-full max-w-md">
      <div className="flex flex-col gap-3 sm:flex-row">
        <input
          id={id}
          type="email"
          value={email}
          onChange={(e) => {
            setEmail(e.target.value);
            if (status === "error") setStatus("idle");
          }}
          onKeyDown={(e) => e.key === "Enter" && submit()}
          placeholder="you@example.com"
          className={`flex-1 rounded-xl border px-4 py-3 text-base outline-none transition focus:ring-2 focus:ring-emerald-500 ${
            dark
              ? "border-emerald-700 bg-emerald-950 text-white placeholder-emerald-400"
              : "border-gray-300 bg-white text-gray-900 placeholder-gray-400"
          }`}
        />
        <button
          onClick={submit}
          disabled={status === "loading"}
          className="flex items-center justify-center gap-2 rounded-xl bg-emerald-600 px-6 py-3 font-semibold text-white transition hover:bg-emerald-700 disabled:opacity-60"
        >
          {status === "loading" ? "Joining…" : "Get early access"}
          <ArrowRight className="h-4 w-4" />
        </button>
      </div>
      {status === "error" && (
        <p className={`mt-2 text-sm ${dark ? "text-amber-300" : "text-red-600"}`}>
          Please enter a valid email — or try again in a moment.
        </p>
      )}
      <p className={`mt-2 text-sm ${dark ? "text-emerald-300" : "text-gray-500"}`}>
        Free during early access. No spam, ever.
      </p>
    </div>
  );
}
