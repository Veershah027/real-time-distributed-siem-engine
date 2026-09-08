import type { DetectionRule } from "@/types";

/** Human-readable trigger condition, built from the rule's live parameters. */
export function ruleCondition(rule: DetectionRule | undefined, ruleId: string): string {
  const p = (rule?.parameters ?? {}) as Record<string, number>;
  switch (rule?.rule_id ?? ruleId) {
    case "RULE-001":
      return `> ${p.max_failures ?? 10} failed authentication attempts from one source IP within ${p.window_seconds ?? 60}s`;
    case "RULE-002":
      return `one source IP attempts authentication against > ${p.unique_users ?? 8} distinct usernames within ${p.window_seconds ?? 120}s`;
    case "RULE-003":
      return `one source IP contacts > ${p.unique_ports ?? 20} unique destination ports within ${p.window_seconds ?? 30}s`;
    case "RULE-004":
      return "a non-privileged account performs an administrative action, off-hours, or the host reports an explicit privilege-escalation event";
    case "RULE-005":
      return "synthetic database log text matches an injection / exfiltration pattern, or returns an abnormally large result set";
    case "RULE-006":
      return `sliding-window outbound bytes for a source→destination pair exceed ${((p.bytes_threshold ?? 52428800) / 1048576).toFixed(0)} MiB within ${p.window_seconds ?? 60}s`;
    case "RULE-007":
      return `one account authenticates successfully from > ${p.distinct_ips ?? 4} distinct source IPs within ${p.window_seconds ?? 300}s`;
    case "ANOM-001":
      return `a per-minute metric deviates > ${p.zscore_threshold ?? 3.5}σ from its rolling EWMA baseline (min ${p.min_samples ?? 20} samples)`;
    case "ML-001":
      return "an Isolation Forest trained on recent per-minute feature vectors flags the current minute as an outlier";
    default:
      return rule?.description ?? "See detection engine source.";
  }
}
