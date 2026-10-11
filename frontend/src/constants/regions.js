/**
 * Validated regions for ISMPCE.
 * Restricted strictly to National level and the 12 empirical state-level jurisdictions
 * trained and cross-validated on Climate TRACE satellite observations & EDGAR gridded timeseries.
 */
export const NIGERIA_REGIONS = [
  "Nigeria (National)",
  "Bauchi (Case Study)",
  "Lagos",
  "Rivers",
  "Delta",
  "Akwa Ibom",
  "Kano",
  "Ogun",
  "Kaduna",
  "Oyo",
  "FCT Abuja",
  "Kogi",
  "Borno",
];

export function cleanRegionName(region) {
  if (!region) return "Nigeria";
  return region.replace(" (National)", "").replace(" (Case Study)", "").trim();
}

export function isNationalRegion(region) {
  if (!region) return true;
  const clean = cleanRegionName(region).toLowerCase();
  return clean === "nigeria" || clean === "national";
}
