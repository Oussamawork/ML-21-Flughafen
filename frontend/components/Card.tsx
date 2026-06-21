import type { ReactNode } from "react";

// Shared card frame + header (mirrors .flight-card/.section-title in styles.css).
export function Card({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <article
      className={`min-w-0 rounded-lg border border-white/85 bg-panel p-[18px] shadow-card backdrop-blur-[18px] ${className}`}
    >
      {children}
    </article>
  );
}

export function SectionTitle({
  title,
  badge,
}: {
  title: string;
  badge?: ReactNode;
}) {
  return (
    <div className="mb-3.5 flex items-baseline justify-between gap-3.5">
      <p className="m-0 font-[950]">{title}</p>
      {badge != null && (
        <span className="text-[13px] font-[850] text-muted">{badge}</span>
      )}
    </div>
  );
}
