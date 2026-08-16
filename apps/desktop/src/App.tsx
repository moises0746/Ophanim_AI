import {
  Group,
  Internet,
  Puzzle,
  Settings,
  TaskList,
  Folder,
} from 'iconoir-react';
import { HashRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AppShell } from './app/AppShell';
import { ApprovalModal } from './components/ApprovalModal';
import { ActivityPage } from './features/activity/ActivityPage';
import { ApprovalsPage } from './features/activity/ApprovalsPage';
import { AssistantPage } from './features/assistant/AssistantPage';
import { AutomationsPage } from './features/automations/AutomationsPage';
import { KnowledgePage } from './features/knowledge/KnowledgePage';
import { ModelsPage } from './features/models/ModelsPage';
import { UnavailablePage } from './features/shared/UnavailablePage';
import { SystemHealthPage } from './features/system/SystemHealthPage';
import { useAssistantWorkspace } from './hooks/useAssistantWorkspace';
import type { AssistantEventStreamClient } from './services/eventStream';
import type { AssistantRuntimeClient } from './services/runtime';

interface AppProps {
  eventStreamClient?: AssistantEventStreamClient;
  runtimeClient?: AssistantRuntimeClient;
}

export function App({ eventStreamClient, runtimeClient }: AppProps) {
  const workspace = useAssistantWorkspace({ eventStreamClient, runtimeClient });

  return (
    <HashRouter>
      <AppShell
        connection={workspace.connection}
        models={workspace.models}
        selectedModelKey={workspace.selectedModelKey}
        routingMode={workspace.routingMode}
        onModelChange={workspace.changeModel}
        onRoutingChange={workspace.setRoutingMode}
      >
        <Routes>
          <Route path="/" element={<AssistantPage workspace={workspace} />} />
          <Route path="/models" element={<ModelsPage models={workspace.models} selectedModelKey={workspace.selectedModelKey} connection={workspace.connection} onSelect={workspace.changeModel} />} />
          <Route path="/knowledge" element={<KnowledgePage citations={workspace.citations} />} />
          <Route path="/automations" element={<AutomationsPage />} />
          <Route path="/system-health" element={<SystemHealthPage connection={workspace.connection} models={workspace.models} eventCount={workspace.events.length} providerStatus={workspace.providerStatus} />} />
          <Route path="/activity" element={<ActivityPage events={workspace.events} />} />
          <Route path="/approvals" element={<ApprovalsPage request={workspace.pendingApproval} onDismiss={workspace.dismissApproval} />} />
          <Route path="/tasks" element={<UnavailablePage eyebrow="Work" title="Tasks" description="Authoritative task state and bounded execution history." detail="The current Desktop runtime does not expose a task-list contract. Assistant chat and Core events remain available without fabricating task records." icon={TaskList} />} />
          <Route path="/projects" element={<UnavailablePage eyebrow="Work" title="Projects" description="Organized goals, tasks, outputs, and evidence." detail="Project persistence and membership contracts are not implemented in the connected runtime." icon={Folder} />} />
          <Route path="/ai-team" element={<UnavailablePage eyebrow="Agents" title="AI Team" description="Bounded capability profiles and event-derived assignments." detail="The UI will show agents only after Core exposes authorized agent-profile and assignment projections." icon={Group} />} />
          <Route path="/browser" element={<UnavailablePage eyebrow="Capabilities" title="Browser" description="Governed read-only browser investigation." detail="Browser automation is not part of this UI task. No browser control or synthetic session is exposed here." icon={Internet} />} />
          <Route path="/integrations" element={<UnavailablePage eyebrow="Connections" title="Integrations" description="Typed, governed connections to external systems." detail="Integration registry and health contracts are not exposed to Desktop yet. Provider credentials remain outside React." icon={Puzzle} />} />
          <Route path="/settings" element={<UnavailablePage eyebrow="Preferences" title="Settings" description="Workspace, accessibility, privacy, and runtime preferences." detail="Persistent settings are not implemented. System reduced-motion and high-contrast preferences are honored automatically." icon={Settings} />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AppShell>

      <ApprovalModal
        request={workspace.pendingApproval}
        onApprove={workspace.dismissApproval}
        onReject={workspace.dismissApproval}
      />
    </HashRouter>
  );
}

export default App;
