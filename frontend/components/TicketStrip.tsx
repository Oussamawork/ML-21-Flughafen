"use client";

// Mirrors SkyGuide's .ticket-strip (flight no · Language · "I am here" · Load).
export type UiLanguage = "en" | "fr" | "darija";
export type Position =
  | "entrance"
  | "check-in"
  | "security"
  | "duty-free"
  | "pharmacy";

interface Props {
  flightNumber: string;
  onFlightNumber: (v: string) => void;
  language: UiLanguage;
  onLanguage: (v: UiLanguage) => void;
  position: Position;
  onPosition: (v: Position) => void;
  onLoad: () => void;
  loading: boolean;
}

const FIELD =
  "min-h-[48px] w-full rounded-lg border border-line bg-white px-3 font-[800] text-ink";
const LABEL = "grid gap-[7px] text-[13px] font-[850] text-[#3f4a58]";

export function TicketStrip({
  flightNumber,
  onFlightNumber,
  language,
  onLanguage,
  position,
  onPosition,
  onLoad,
  loading,
}: Props) {
  return (
    <section className="mx-auto mb-[18px] grid max-w-[1240px] grid-cols-[1.1fr_.7fr_.9fr_auto] items-end gap-3 px-[clamp(18px,4vw,58px)] max-[980px]:grid-cols-1">
      <label className={LABEL}>
        Flight or ticket number
        <input
          value={flightNumber}
          placeholder="Enter flight number"
          onChange={(e) => onFlightNumber(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && onLoad()}
          className={FIELD}
        />
      </label>
      <label className={LABEL}>
        Language
        <select
          value={language}
          onChange={(e) => onLanguage(e.target.value as UiLanguage)}
          className={FIELD}
        >
          <option value="en">English</option>
          <option value="fr">Français</option>
          <option value="darija">Darija</option>
        </select>
      </label>
      <label className={LABEL}>
        I am here
        <select
          value={position}
          onChange={(e) => onPosition(e.target.value as Position)}
          className={FIELD}
        >
          <option value="entrance">Main entrance</option>
          <option value="check-in">Check-in hall</option>
          <option value="security">Security control</option>
          <option value="duty-free">Duty free area</option>
          <option value="pharmacy">Airport pharmacy</option>
        </select>
      </label>
      <button
        type="button"
        onClick={onLoad}
        disabled={loading}
        className="min-h-[48px] rounded-lg bg-red px-[18px] font-[950] text-white shadow-[0_16px_34px_rgba(223,31,61,.22)] disabled:opacity-60"
      >
        Load flight
      </button>
    </section>
  );
}
