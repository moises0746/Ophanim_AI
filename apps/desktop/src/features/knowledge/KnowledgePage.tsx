import { Book, Database, InfoCircle as InfoEmpty } from 'iconoir-react';
import type { CitationItem } from '../../types/events';
import { PageScaffold } from '../shared/PageScaffold';

export function KnowledgePage({ citations }: { citations: CitationItem[] }) {
  return (
    <PageScaffold eyebrow="Knowledge" title="Knowledge Vault" description="Verified citations and source provenance from the current authorized session.">
      <div className="knowledge-layout">
        <aside className="surface vault-sidebar"><h2>Vault</h2><button type="button" className="is-active"><Book width={17} height={17} aria-hidden /> Current session <span>{citations.length}</span></button><button type="button" disabled title="Document browsing is not connected"><Database width={17} height={17} aria-hidden /> Documents</button></aside>
        <section className="surface section-card">
          <header className="section-header"><div><h2>Verified sources</h2><p>Only Core-provided citations are displayed.</p></div></header>
          {citations.length === 0 ? <div className="large-empty"><InfoEmpty width={28} height={28} aria-hidden /><h3>No citations in this session</h3><p>Ask a grounded question through a connected knowledge adapter. Ophanim will not invent document counts, relevance scores, or source links.</p></div> : <div className="citation-grid">{citations.map((citation) => <article key={citation.citationId}><strong>{citation.documentTitle}</strong><span>{citation.headerPath}</span><p>{citation.excerpt}</p><small>Score {citation.score}</small></article>)}</div>}
        </section>
      </div>
    </PageScaffold>
  );
}
