import { Route, Routes } from "react-router-dom";
import { RealtimeProvider } from "@/hooks/realtimeContext";
import { Layout } from "@/components/Layout";
import { Dashboard } from "@/pages/Dashboard";
import { Events } from "@/pages/Events";
import { Alerts } from "@/pages/Alerts";
import { Detections } from "@/pages/Detections";
import { Threats } from "@/pages/Threats";
import { Simulator } from "@/pages/Simulator";
import { System } from "@/pages/System";

export default function App() {
  return (
    <RealtimeProvider>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/events" element={<Events />} />
          <Route path="/alerts" element={<Alerts />} />
          <Route path="/detections" element={<Detections />} />
          <Route path="/threats" element={<Threats />} />
          <Route path="/simulator" element={<Simulator />} />
          <Route path="/system" element={<System />} />
          <Route
            path="*"
            element={<div className="p-8 text-slate-400">Page not found.</div>}
          />
        </Routes>
      </Layout>
    </RealtimeProvider>
  );
}
