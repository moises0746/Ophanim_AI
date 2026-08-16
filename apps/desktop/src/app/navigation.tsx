import type { ForwardRefExoticComponent, RefAttributes, SVGProps } from 'react';
import {
  LayoutDashboard,
  MessageSquare,
  Users,
  GitBranch,
  FileText,
  Database,
  Cpu,
  Zap,
  Plug,
  BarChart,
  Settings,
} from 'lucide-react';

export interface NavigationItem {
  label: string;
  path: string;
  icon: ForwardRefExoticComponent<Omit<SVGProps<SVGSVGElement>, 'ref'> & RefAttributes<SVGSVGElement>>;
  end?: boolean;
}

export const primaryNavigation: NavigationItem[] = [
  { label: 'Dashboard', path: '/', icon: LayoutDashboard, end: true },
  { label: 'Chat', path: '/chat', icon: MessageSquare },
  { label: 'Agents', path: '/agents', icon: Users },
  { label: 'Workflows', path: '/workflows', icon: GitBranch },
  { label: 'Documents', path: '/documents', icon: FileText },
  { label: 'Knowledge Vault', path: '/knowledge', icon: Database },
];

export const operationsNavigation: NavigationItem[] = [
  { label: 'Models & Runtimes', path: '/models', icon: Cpu },
  { label: 'Automations', path: '/automations', icon: Zap },
  { label: 'Integrations', path: '/integrations', icon: Plug },
  { label: 'Analytics', path: '/analytics', icon: BarChart },
  { label: 'Settings', path: '/settings', icon: Settings },
];

export const allNavigation = [...primaryNavigation, ...operationsNavigation];

export const routeTitles = new Map(
  allNavigation.map((item) => [item.path, item.label]),
);
