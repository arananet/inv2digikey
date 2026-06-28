// ── Inventory search filtering ──────────────────────────────────────────────────
// Pure, client-side filtering for the inventory search bar. Kept as an ES module
// (no DOM/state access) so it can be unit-tested with Node and imported by index.html.

// Fields the user can target from the search bar. 'all' spans every text field.
export const SEARCH_FIELDS = [
  { key: 'all',             label: 'All' },
  { key: 'digikey_pn',      label: 'Reference' },
  { key: 'manufacturer_pn', label: 'Mfr ref' },
  { key: 'description',     label: 'Description' },
  { key: 'manufacturer',    label: 'Manufacturer' },
  { key: 'location',        label: 'Location' },
];

const ALL_KEYS = ['digikey_pn', 'manufacturer_pn', 'description', 'manufacturer', 'location'];

// Returns the components whose chosen field(s) contain `term` (case-insensitive,
// substring). An empty/whitespace term returns the list unchanged. An unknown or
// 'all' field searches across every text field.
export function filterComponents(components, term, field) {
  const q = String(term ?? '').trim().toLowerCase();
  if (!q) return components;
  const keys = (!field || field === 'all') ? ALL_KEYS : [field];
  return components.filter(c => keys.some(k => String(c[k] ?? '').toLowerCase().includes(q)));
}
