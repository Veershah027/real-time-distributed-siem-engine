import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Icon } from "@/components/ui/Icon";
import { Kbd } from "@/components/ui/primitives";

const IP_RE = /^\d{1,3}(\.\d{1,3}){3}$/;

export function CommandSearch() {
  const [q, setQ] = useState("");
  const ref = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        ref.current?.focus();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    const term = q.trim();
    if (!term) return;
    if (IP_RE.test(term)) navigate(`/events?source_ip=${encodeURIComponent(term)}`);
    else navigate(`/events?q=${encodeURIComponent(term)}`);
    setQ("");
    ref.current?.blur();
  };

  return (
    <form onSubmit={submit} className="relative hidden md:block">
      <Icon.search
        size={13}
        className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 text-faint"
      />
      <input
        ref={ref}
        value={q}
        onChange={(e) => setQ(e.target.value)}
        placeholder="Search events by IP or text"
        aria-label="Search events"
        className="input h-8 w-64 pl-8 pr-14 text-[12px]"
      />
      <span className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2">
        <Kbd>⌘K</Kbd>
      </span>
    </form>
  );
}
