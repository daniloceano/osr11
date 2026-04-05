import { redirect } from 'next/navigation';

export default function TidalSensitivityRedirect() {
  redirect('/results/threshold-calibration/tidal-sensitivity');
}
