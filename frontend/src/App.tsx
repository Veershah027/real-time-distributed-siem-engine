import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "@/components/shell/AppShell";
import { Overview } from "@/pages/Overview";
import { LiveEvents } from "@/pages/LiveEvents";
import { Alerts } from "@/pages/Alerts";
import { DetectionRules } from "@/pages/DetectionRules";
import { Anomalies } from "@/pages/Anomalies";
import { ThreatActivity } from "@/pages/ThreatActivity";
import { EventAnalytics } from "@/pages/EventAnalytics";
import { SourceAnalytics } from "@/pages/SourceAnalytics";
import { Performance } from "@/pages/Performance";
import { Simulator } from "@/pages/Simulator";
import { Scenarios } from "@/pages/Scenarios";
import { Infrastructure } from "@/pages/Infrastructure";
import { Settings } from "@/pages/Settings";

export default function App() {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<Overview />} />
        <Route path="/events" element={<LiveEvents />} />
        <Route path="/alerts" element={<Alerts />} />
        <Route path="/alerts/:alertId" element={<Alerts />} />
        <Route path="/rules" element={<DetectionRules />} />
        <Route path="/anomalies" element={<Anomalies />} />
        <Route path="/threats" element={<ThreatActivity />} />
        <Route path="/analytics/events" element={<EventAnalytics />} />
        <Route path="/analytics/sources" element={<SourceAnalytics />} />
        <Route path="/analytics/performance" element={<Performance />} />
        <Route path="/simulator" element={<Simulator />} />
        <Route path="/scenarios" element={<Scenarios />} />
        <Route path="/infrastructure" element={<Infrastructure />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AppShell>
  );
}
