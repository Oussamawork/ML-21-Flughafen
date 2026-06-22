"use client";

// Mirrors SkyGuide's .nav / .compact-nav.
interface Props {
  variant: "home" | "app";
  onHome?: () => void;
}

const PILL =
  "rounded-lg border border-white/70 bg-white/[.64] px-[11px] py-2 text-[13px] font-[850] text-[#334052]";

function Brand() {
  return (
    <div className="inline-flex items-center gap-2.5 font-[950]">
      <span className="grid h-[38px] w-[38px] place-items-center rounded-lg bg-red text-[13px] text-white">
        SG
      </span>
      <span>SkyGuide AUH</span>
    </div>
  );
}

export function TopNav({ variant, onHome }: Props) {
  return (
    <nav
      className={`relative z-[2] mx-auto flex max-w-[1240px] items-center justify-between gap-[18px] ${
        variant === "app" ? "px-[clamp(18px,4vw,58px)] py-6" : ""
      } max-[640px]:flex-col max-[640px]:items-start`}
    >
      <Brand />
      {variant === "home" ? (
        <div className="flex flex-wrap justify-end gap-2">
          <span className={PILL}>Arabic · Darija · French · English</span>
          <span className={PILL}>Voice + Text</span>
        </div>
      ) : (
        <button type="button" onClick={onHome} className={PILL}>
          Home
        </button>
      )}
    </nav>
  );
}
