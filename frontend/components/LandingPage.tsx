"use client";

import { TopNav } from "./TopNav";

// Mirrors SkyGuide's #homePage (hero + animated clouds + prep grid).
interface Props {
  onEnter: () => void;
}

const PREP = [
  { icon: "▣", title: "Save your bag", body: "Find your baggage belt instantly and avoid searching screens inside the terminal.", cta: "Find baggage →" },
  { icon: "◷", title: "Save your time", body: "Know how many meters and minutes are left before you start walking.", cta: "Check distance →" },
  { icon: "⌖", title: "Gate guidance", body: "Follow a clear route from your current position to the right boarding gate.", cta: "Guide me →" },
  { icon: "✦", title: "Smart support", body: "Ask the agent in English, French, or Darija and get a spoken answer.", cta: "Ask SkyGuide →" },
  { icon: "▤", title: "Flight details", body: "See terminal, gate, check-in zone, baggage belt, boarding time, and status.", cta: "Open ticket →" },
  { icon: "◉", title: "Map destinations", body: "Click any point on the airport map and hear the route and distance.", cta: "Explore map →" },
];

const CLOUD = "absolute h-[12vw] w-[36vw] rounded-full bg-white/[.38] blur-[24px] animate-cloud";

export function LandingPage({ onEnter }: Props) {
  return (
    <section className="relative min-h-screen overflow-hidden px-[clamp(18px,4vw,58px)] py-7 bg-[linear-gradient(90deg,rgba(255,255,255,.96),rgba(255,255,255,.62),rgba(255,255,255,.08)),url('/assets/airport-sky-hero.png')] bg-cover bg-center bg-no-repeat">
      <div className={`${CLOUD} left-[-20%] top-[18%]`} />
      <div className={`${CLOUD} left-[15%] top-[62%] [animation-duration:38s]`} />
      <div className={`${CLOUD} left-[60%] top-[34%] [animation-duration:44s]`} />

      <TopNav variant="home" />

      <section className="relative z-[2] mx-auto mt-[18vh] max-w-[1240px] max-[980px]:mt-[12vh]">
        <p className="m-0 mb-3.5 text-xs font-[950] uppercase text-red">
          Sheikh Zayed International Airport
        </p>
        <h1 className="m-0 max-w-[680px] text-[clamp(54px,8vw,104px)] leading-[.95]">
          Your Guide in the Sky.
        </h1>
        <p className="mt-[22px] max-w-[640px] text-[clamp(17px,2vw,21px)] leading-[1.55] text-[#3f4a58]">
          A multilingual airport agent that reads your flight ticket, understands your
          questions, and guides you through the terminal with live distance and route
          instructions.
        </p>
        <button
          type="button"
          onClick={onEnter}
          className="mt-7 min-h-[48px] rounded-lg bg-red px-[18px] font-[950] text-white shadow-[0_16px_34px_rgba(223,31,61,.22)]"
        >
          Enter flight ticket
        </button>
      </section>

      <section className="relative z-[2] mx-auto mt-[16vh] max-w-[1240px] pb-[70px] max-[980px]:mt-[10vh]">
        <p className="m-0 mb-3 text-center text-sm font-[950] uppercase tracking-[.32em] text-[#0d8f8c] max-[640px]:text-left max-[640px]:tracking-[.2em]">
          Trip ready?
        </p>
        <h2 className="m-0 mb-[46px] text-center text-[clamp(34px,4vw,52px)] text-[#18343a] max-[640px]:text-left">
          Prepare for your airport journey
        </h2>
        <div className="grid grid-cols-3 gap-[18px] max-[980px]:grid-cols-2 max-[640px]:grid-cols-1">
          {PREP.map((p) => (
            <article
              key={p.title}
              className="grid min-h-[280px] content-start gap-[18px] rounded-lg border border-white/90 bg-white/[.86] p-8 shadow-[0_22px_58px_rgba(27,53,86,.12)] backdrop-blur-[16px] transition hover:-translate-y-[5px] hover:shadow-[0_30px_70px_rgba(27,53,86,.18)] max-[640px]:min-h-[220px]"
            >
              <div className="grid h-16 w-16 place-items-center rounded-full bg-[#f2f5f5] text-[28px] text-[#18343a]">
                {p.icon}
              </div>
              <h3 className="m-0 text-[25px] leading-[1.15] text-[#18343a]">{p.title}</h3>
              <p className="m-0 text-base leading-[1.55] text-[#687174]">{p.body}</p>
              <span className="mt-2.5 font-[950] text-[#0d8f8c]">{p.cta}</span>
            </article>
          ))}
        </div>
      </section>
    </section>
  );
}
