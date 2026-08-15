import type { ForwardRefExoticComponent, RefAttributes, SVGProps } from 'react';
import {
  Activity,
  Book,
  ChatBubble,
  Dashboard,
  Database,
  Flash,
  Folder,
  Group,
  Internet,
  Puzzle,
  Settings,
  ShieldCheck,
  SystemRestart,
  TaskList,
} from 'iconoir-react';

export interface NavigationItem {
  label: string;
  path: string;
  icon: ForwardRefExoticComponent<Omit<SVGProps<SVGSVGElement>, 'ref'> & RefAttributes<SVGSVGElement>>;
  end?: boolean;
}

export const primaryNavigation: NavigationItem[] = [
  { label: 'Assistant', path: '/', icon: ChatBubble, end: true },
  { label: 'Tasks', path: '/tasks', icon: TaskList },
  { label: 'Projects', path: '/projects', icon: Folder },
  { label: 'AI Team', path: '/ai-team', icon: Group },
  { label: 'Knowledge', path: '/knowledge', icon: Book },
  { label: 'Automations', path: '/automations', icon: Flash },
  { label: 'Browser', path: '/browser', icon: Internet },
];

export const operationsNavigation: NavigationItem[] = [
  { label: 'Approvals', path: '/approvals', icon: ShieldCheck },
  { label: 'Activity', path: '/activity', icon: Activity },
  { label: 'Integrations', path: '/integrations', icon: Puzzle },
  { label: 'Models & Runtimes', path: '/models', icon: Database },
  { label: 'System Health', path: '/system-health', icon: SystemRestart },
  { label: 'Settings', path: '/settings', icon: Settings },
];

export const allNavigation = [...primaryNavigation, ...operationsNavigation];

export const routeTitles = new Map(
  allNavigation.map((item) => [item.path, item.label]),
);

export const DashboardIcon = Dashboard;
