import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router-dom";

import { AppShell } from "./components/AppShell";
import { ConflictCenterPage } from "./pages/ConflictCenterPage";
import { DashboardPage } from "./pages/DashboardPage";
import { EvalsPage } from "./pages/EvalsPage";
import { ExplainCenterPage } from "./pages/ExplainCenterPage";
import { ExplorerPage } from "./pages/ExplorerPage";
import { IngestionCenterPage } from "./pages/IngestionCenterPage";
import { OperationsPage } from "./pages/OperationsPage";
import { QueryStudioPage } from "./pages/QueryStudioPage";
import { SettingsPage } from "./pages/SettingsPage";
import { TimelinePage } from "./pages/TimelinePage";

const queryClient = new QueryClient();

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<AppShell />}>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/explorer" element={<ExplorerPage />} />
            <Route path="/timeline" element={<TimelinePage />} />
            <Route path="/query" element={<QueryStudioPage />} />
            <Route path="/explain" element={<ExplainCenterPage />} />
            <Route path="/conflicts" element={<ConflictCenterPage />} />
            <Route path="/ingestion" element={<IngestionCenterPage />} />
            <Route path="/operations" element={<OperationsPage />} />
            <Route path="/evals" element={<EvalsPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
