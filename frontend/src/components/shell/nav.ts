import type { IconName } from "@/components/ui/Icon";

export interface NavItem {
  to: string;
  label: string;
  icon: IconName;
  end?: boolean;
}
export interface NavGroup {
  label: string;
  items: NavItem[];
}

export const NAV: NavGroup[] = [
  {
    label: "Monitor",
    items: [
      { to: "/", label: "Overview", icon: "overview", end: true },
      { to: "/events", label: "Live Events", icon: "activity" },
      { to: "/alerts", label: "Alerts", icon: "alert" },
    ],
  },
  {
    label: "Detection",
    items: [
      { to: "/rules", label: "Detection Rules", icon: "rules" },
      { to: "/anomalies", label: "Anomalies", icon: "anomaly" },
      { to: "/threats", label: "Threat Activity", icon: "target" },
    ],
  },
  {
    label: "Analytics",
    items: [
      { to: "/analytics/events", label: "Event Analytics", icon: "chart" },
      { to: "/analytics/sources", label: "Source Analytics", icon: "globe" },
      { to: "/analytics/performance", label: "Performance", icon: "gauge" },
    ],
  },
  {
    label: "Simulation",
    items: [
      { to: "/simulator", label: "Attack Simulator", icon: "play" },
      { to: "/scenarios", label: "Demo Scenarios", icon: "scenarios" },
    ],
  },
  {
    label: "System",
    items: [
      { to: "/infrastructure", label: "Infrastructure", icon: "server" },
      { to: "/settings", label: "Settings", icon: "settings" },
    ],
  },
];
