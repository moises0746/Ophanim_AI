import { useEffect, useRef, useState, type ReactNode } from 'react';
import {
  Bell,
  Menu,
  ChevronDown as NavArrowDown,
  Search,
  PanelLeftClose as SidebarCollapse,
  UserCircle,
  X as Xmark,
} from 'lucide-react';
import { NavLink, useLocation, useNavigate } from 'react-router-dom';
import type {
  AssistantModel,
  RoutingMode,
  RuntimeConnectionState,
} from '../types/events';
import {
  allNavigation,
  operationsNavigation,
  primaryNavigation,
  routeTitles,
  type NavigationItem,
} from './navigation';

const ophanimMark = new URL('../../src-tauri/icons/ophanim.png', import.meta.url).href;

interface AppShellProps {
  children: ReactNode;
  connection: RuntimeConnectionState;
  models: AssistantModel[];
  selectedModelKey: string;
  routingMode: RoutingMode;
  onModelChange: (modelKey: string) => void;
  onRoutingChange: (mode: RoutingMode) => void;
}

const NavigationSection = ({
  items,
  collapsed,
  onNavigate,
}: {
  items: NavigationItem[];
  collapsed: boolean;
  onNavigate: () => void;
}) => (
  <nav className="sidebar-nav" aria-label={items === primaryNavigation ? 'Primary' : 'Operations'}>
    {items.map(({ label, path, icon: Icon, end }) => (
      <NavLink
        key={path}
        to={path}
        end={end}
        onClick={onNavigate}
        className={({ isActive }) => `nav-item${isActive ? ' is-active' : ''}`}
        title={collapsed ? label : undefined}
      >
        <Icon width={19} height={19} aria-hidden />
        <span className="nav-label">{label}</span>
      </NavLink>
    ))}
  </nav>
);

export function AppShell({
  children,
  connection,
  models,
  selectedModelKey,
  routingMode,
  onModelChange,
  onRoutingChange,
}: AppShellProps) {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [searchValue, setSearchValue] = useState('');
  const searchInputRef = useRef<HTMLInputElement>(null);
  const location = useLocation();
  const navigate = useNavigate();
  const selectedModel = models.find(
    (model) => `${model.provider}:${model.model_id}` === selectedModelKey,
  );

  useEffect(() => setMobileOpen(false), [location.pathname]);
  useEffect(() => {
    const focusSearch = (event: KeyboardEvent) => {
      if (event.ctrlKey && event.key.toLowerCase() === 'k') {
        event.preventDefault();
        searchInputRef.current?.focus();
      }
    };
    window.addEventListener('keydown', focusSearch);
    return () => window.removeEventListener('keydown', focusSearch);
  }, []);

  const submitSearch = () => {
    const normalized = searchValue.trim().toLowerCase();
    if (!normalized) return;
    const route = allNavigation.find((item) => item.label.toLowerCase().includes(normalized));
    if (route) {
      navigate(route.path);
      setSearchValue('');
    }
  };

  return (
    <div className={`app-shell${collapsed ? ' sidebar-collapsed' : ''}`}>
      <a className="skip-link" href="#main-content">Skip to content</a>
      <aside className={`app-sidebar${mobileOpen ? ' is-open' : ''}`} aria-label="Workspace navigation">
        <div className="brand-lockup">
          <img src={ophanimMark} alt="" className="brand-mark" />
          <div className="brand-copy">
            <strong>OPHANIM</strong>
            <span>AI Orchestrator</span>
          </div>
          <button
            type="button"
            className="icon-button sidebar-close"
            aria-label="Close navigation"
            onClick={() => setMobileOpen(false)}
          >
            <Xmark width={20} height={20} aria-hidden />
          </button>
        </div>

        <div className="workspace-switcher" aria-label="Current workspace">
          <span className="workspace-status" aria-hidden />
          <span className="nav-label">Local workspace</span>
          <NavArrowDown width={15} height={15} aria-hidden className="nav-label" />
        </div>

        <NavigationSection items={primaryNavigation} collapsed={collapsed} onNavigate={() => setMobileOpen(false)} />
        <div className="sidebar-separator" />
        <NavigationSection items={operationsNavigation} collapsed={collapsed} onNavigate={() => setMobileOpen(false)} />

        <div className="sidebar-footer">
          <div className={`runtime-summary status-${connection}`}>
            <span className="runtime-dot" aria-hidden />
            <span className="nav-label">
              <strong>{connection === 'online' ? 'Core connected' : 'Core unavailable'}</strong>
              <small>{models.length} configured model{models.length === 1 ? '' : 's'}</small>
            </span>
          </div>
          <button
            type="button"
            className="collapse-button"
            onClick={() => setCollapsed((value) => !value)}
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            <SidebarCollapse width={18} height={18} aria-hidden />
            <span className="nav-label">Collapse</span>
          </button>
        </div>
      </aside>

      {mobileOpen && <button className="sidebar-scrim" aria-label="Close navigation" onClick={() => setMobileOpen(false)} />}

      <div className="app-frame">
        <header className="topbar">
          <div className="topbar-title">
            <button
              type="button"
              className="icon-button mobile-menu"
              aria-label="Open navigation"
              onClick={() => setMobileOpen(true)}
            >
              <Menu width={21} height={21} aria-hidden />
            </button>
            <div>
              <span className="eyebrow">Workspace</span>
              <strong>{routeTitles.get(location.pathname) ?? 'Ophanim'}</strong>
            </div>
          </div>

          <div className="global-search" role="search">
            <Search width={17} height={17} aria-hidden />
            <input
              ref={searchInputRef}
              value={searchValue}
              onChange={(event) => setSearchValue(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter') submitSearch();
              }}
              aria-label="Search workspace routes"
              placeholder="Search workspace"
              list="workspace-routes"
            />
            <datalist id="workspace-routes">
              {allNavigation.map((item) => <option key={item.path} value={item.label} />)}
            </datalist>
            <kbd>Ctrl K</kbd>
          </div>

          <div className="topbar-controls">
            <label className="compact-select">
              <span className="sr-only">Routing mode</span>
              <select value={routingMode} onChange={(event) => onRoutingChange(event.target.value as RoutingMode)}>
                <option value="LOCAL_ONLY">Local only</option>
                <option value="CLOUD_ONLY">Cloud Only</option>
                <option value="HYBRID_ROUTED">Hybrid / Cloud Assisted</option>
              </select>
              <NavArrowDown width={14} height={14} aria-hidden />
            </label>
            <label className="compact-select model-select">
              <span className="sr-only">Active model</span>
              <select value={selectedModelKey} onChange={(event) => onModelChange(event.target.value)} disabled={models.length === 0}>
                {models.length === 0 && <option value="">No model</option>}
                {models.map((model) => (
                  <option key={`${model.provider}:${model.model_id}`} value={`${model.provider}:${model.model_id}`}>
                    {model.display_name}
                  </option>
                ))}
              </select>
              <NavArrowDown width={14} height={14} aria-hidden />
            </label>
            <button type="button" className="icon-button" aria-label="Notifications unavailable" title="Notifications are not connected yet">
              <Bell width={19} height={19} aria-hidden />
            </button>
            <button type="button" className="profile-button" aria-label="Open profile menu" title="Local profile">
              <UserCircle width={24} height={24} aria-hidden />
              <span><strong>Local operator</strong><small>{selectedModel?.is_local === false ? 'Cloud assisted' : 'Local session'}</small></span>
              <NavArrowDown width={14} height={14} aria-hidden />
            </button>
          </div>
        </header>

        <main id="main-content" className="app-content" tabIndex={-1}>{children}</main>
      </div>
    </div>
  );
}
