import type { ForwardRefExoticComponent, RefAttributes, SVGProps } from 'react';
import { InfoCircle } from 'iconoir-react';
import { PageScaffold } from './PageScaffold';

interface UnavailablePageProps {
  eyebrow: string;
  title: string;
  description: string;
  detail: string;
  icon: ForwardRefExoticComponent<Omit<SVGProps<SVGSVGElement>, 'ref'> & RefAttributes<SVGSVGElement>>;
}

export function UnavailablePage({ eyebrow, title, description, detail, icon: Icon }: UnavailablePageProps) {
  return (
    <PageScaffold eyebrow={eyebrow} title={title} description={description}>
      <section className="surface unavailable-page"><span className="unavailable-icon"><Icon width={30} height={30} aria-hidden /></span><span className="availability-badge"><InfoCircle width={15} height={15} aria-hidden /> Not available in this release</span><h2>{title} is not connected</h2><p>{detail}</p></section>
    </PageScaffold>
  );
}
