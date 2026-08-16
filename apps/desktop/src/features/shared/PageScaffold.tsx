import type { ReactNode } from 'react';

interface PageScaffoldProps {
  eyebrow: string;
  title: string;
  description: string;
  actions?: ReactNode;
  children: ReactNode;
}

export function PageScaffold({ eyebrow, title, description, actions, children }: PageScaffoldProps) {
  return (
    <div className="feature-page">
      <header className="feature-heading">
        <div><span className="eyebrow">{eyebrow}</span><h1>{title}</h1><p>{description}</p></div>
        {actions && <div className="feature-actions">{actions}</div>}
      </header>
      {children}
    </div>
  );
}
