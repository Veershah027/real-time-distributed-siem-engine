import type { SVGProps } from "react";

type P = SVGProps<SVGSVGElement> & { size?: number };

const base = (size = 16): SVGProps<SVGSVGElement> => ({
  width: size,
  height: size,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.75,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
});

export const Icon = {
  overview: ({ size, ...p }: P) => (
    <svg {...base(size)} {...p}>
      <rect x="3" y="3" width="7" height="9" rx="1" />
      <rect x="14" y="3" width="7" height="5" rx="1" />
      <rect x="14" y="12" width="7" height="9" rx="1" />
      <rect x="3" y="16" width="7" height="5" rx="1" />
    </svg>
  ),
  activity: ({ size, ...p }: P) => (
    <svg {...base(size)} {...p}>
      <path d="M3 12h4l3 8 4-16 3 8h4" />
    </svg>
  ),
  alert: ({ size, ...p }: P) => (
    <svg {...base(size)} {...p}>
      <path d="M12 3l9 16H3z" />
      <path d="M12 9v5" />
      <circle cx="12" cy="17" r="0.5" fill="currentColor" />
    </svg>
  ),
  rules: ({ size, ...p }: P) => (
    <svg {...base(size)} {...p}>
      <path d="M4 6h10M4 12h16M4 18h7" />
      <circle cx="18" cy="6" r="2" />
      <circle cx="9" cy="18" r="2" />
    </svg>
  ),
  anomaly: ({ size, ...p }: P) => (
    <svg {...base(size)} {...p}>
      <path d="M3 15c3 0 3-6 6-6s3 8 6 8 3-10 6-10" />
    </svg>
  ),
  target: ({ size, ...p }: P) => (
    <svg {...base(size)} {...p}>
      <circle cx="12" cy="12" r="8" />
      <circle cx="12" cy="12" r="3.5" />
      <path d="M12 2v3M12 19v3M2 12h3M19 12h3" />
    </svg>
  ),
  chart: ({ size, ...p }: P) => (
    <svg {...base(size)} {...p}>
      <path d="M4 20V4M4 20h16" />
      <rect x="8" y="11" width="3" height="6" />
      <rect x="14" y="7" width="3" height="10" />
    </svg>
  ),
  globe: ({ size, ...p }: P) => (
    <svg {...base(size)} {...p}>
      <circle cx="12" cy="12" r="9" />
      <path d="M3 12h18M12 3c3 3 3 15 0 18M12 3c-3 3-3 15 0 18" />
    </svg>
  ),
  gauge: ({ size, ...p }: P) => (
    <svg {...base(size)} {...p}>
      <path d="M4 18a8 8 0 1 1 16 0" />
      <path d="M12 14l4-4" />
    </svg>
  ),
  play: ({ size, ...p }: P) => (
    <svg {...base(size)} {...p}>
      <path d="M7 4l12 8-12 8z" />
    </svg>
  ),
  scenarios: ({ size, ...p }: P) => (
    <svg {...base(size)} {...p}>
      <rect x="3" y="4" width="18" height="5" rx="1" />
      <rect x="3" y="12" width="18" height="5" rx="1" />
      <path d="M7 9v3M17 17v3" />
    </svg>
  ),
  server: ({ size, ...p }: P) => (
    <svg {...base(size)} {...p}>
      <rect x="3" y="4" width="18" height="7" rx="1.5" />
      <rect x="3" y="13" width="18" height="7" rx="1.5" />
      <circle cx="7" cy="7.5" r="0.6" fill="currentColor" />
      <circle cx="7" cy="16.5" r="0.6" fill="currentColor" />
    </svg>
  ),
  settings: ({ size, ...p }: P) => (
    <svg {...base(size)} {...p}>
      <circle cx="12" cy="12" r="3" />
      <path d="M12 2v3M12 19v3M2 12h3M19 12h3M5 5l2 2M17 17l2 2M5 19l2-2M17 7l2-2" />
    </svg>
  ),
  search: ({ size, ...p }: P) => (
    <svg {...base(size)} {...p}>
      <circle cx="11" cy="11" r="7" />
      <path d="M21 21l-4.5-4.5" />
    </svg>
  ),
  refresh: ({ size, ...p }: P) => (
    <svg {...base(size)} {...p}>
      <path d="M21 12a9 9 0 1 1-2.6-6.3" />
      <path d="M21 4v5h-5" />
    </svg>
  ),
  clock: ({ size, ...p }: P) => (
    <svg {...base(size)} {...p}>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v5l3 2" />
    </svg>
  ),
  close: ({ size, ...p }: P) => (
    <svg {...base(size)} {...p}>
      <path d="M6 6l12 12M18 6L6 18" />
    </svg>
  ),
  chevron: ({ size, ...p }: P) => (
    <svg {...base(size)} {...p}>
      <path d="M9 6l6 6-6 6" />
    </svg>
  ),
  menu: ({ size, ...p }: P) => (
    <svg {...base(size)} {...p}>
      <path d="M3 6h18M3 12h18M3 18h18" />
    </svg>
  ),
  pause: ({ size, ...p }: P) => (
    <svg {...base(size)} {...p}>
      <path d="M8 5v14M16 5v14" />
    </svg>
  ),
  copy: ({ size, ...p }: P) => (
    <svg {...base(size)} {...p}>
      <rect x="9" y="9" width="12" height="12" rx="2" />
      <path d="M5 15V5a2 2 0 0 1 2-2h8" />
    </svg>
  ),
  external: ({ size, ...p }: P) => (
    <svg {...base(size)} {...p}>
      <path d="M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5" />
    </svg>
  ),
  filter: ({ size, ...p }: P) => (
    <svg {...base(size)} {...p}>
      <path d="M3 5h18l-7 8v6l-4 2v-8z" />
    </svg>
  ),
  shield: ({ size, ...p }: P) => (
    <svg {...base(size)} {...p}>
      <path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z" />
    </svg>
  ),
  check: ({ size, ...p }: P) => (
    <svg {...base(size)} {...p}>
      <path d="M4 12l5 5L20 6" />
    </svg>
  ),
  bolt: ({ size, ...p }: P) => (
    <svg {...base(size)} {...p}>
      <path d="M13 3L4 14h7l-1 7 9-11h-7z" />
    </svg>
  ),
  arrowDown: ({ size, ...p }: P) => (
    <svg {...base(size)} {...p}>
      <path d="M12 5v14M6 13l6 6 6-6" />
    </svg>
  ),
};

export type IconName = keyof typeof Icon;
