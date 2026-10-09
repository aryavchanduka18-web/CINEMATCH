/** Same thresholds as api/app/services/confidence.py. */
export function agreementLabel(a: number | null | undefined): "High" | "Moderate" | "Low" | null {
  if (a == null) return null;
  return a >= 75 ? "High" : a >= 50 ? "Moderate" : "Low";
}
