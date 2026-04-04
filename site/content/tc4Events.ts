// AUTO-GENERATED — do not edit by hand.
// Regenerate with: python src/04_threshold_calibration/main.py --summary
// or:              python src/04_threshold_calibration/main.py --timeseries

export type Tc4EventEntry = {
  label: string;
  sector: string;
  disasterId: number;
  date: string;           // 'YYYYMMDD'
  slug: string;
  capturedOptimal: boolean;
  capturedAt: Record<string, boolean>;  // '50', '55', …, '90'
};

export const TC4_OPTIMAL_HS_PCT  = 75;
export const TC4_OPTIMAL_SSH_PCT = 75;

export const tc4Events: Tc4EventEntry[] = [];
