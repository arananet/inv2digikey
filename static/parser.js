// ── Distributor barcode / QR parser ────────────────────────────────────────────
// Handles three label families:
//   • DigiKey / Mouser  — ISO/IEC 15434 Data Matrix with GS/RS control characters
//   • TME (tme.eu)      — plain-text QR with space-separated KEY:VALUE tokens
//   • Plain barcodes    — any other code; the raw value becomes the part number
//
// Exported as an ES module so it can be unit-tested with Node and imported by the
// single-page app in index.html.

export function parseBarcode(raw) {
  const GS  = String.fromCharCode(29);
  const RS  = String.fromCharCode(30);
  const EOT = String.fromCharCode(4);
  const strip = s => s.replace(new RegExp(EOT, 'g'), '').trim();

  const result = { digikey_pn: '', manufacturer_pn: '', manufacturer: '', description: '', quantity: 0, raw_barcode: raw };

  const isDigiKey = raw.includes('[)>') || raw.includes(GS) || raw.includes(RS);
  // TME QR codes are plain text (no control chars): space-separated KEY:VALUE
  // tokens plus a tme.eu details URL, e.g.
  //   QTY:5 PN:SN74LS125AD MFR:TEXASINSTRUMENTS MPN:SN74LS125AD PO:7910976/3 https://www.tme.eu/details/SN74LS125AD
  const isTME = !isDigiKey && (/tme\.eu/i.test(raw) || (/(^|\s)QTY:/i.test(raw) && /(^|\s)MPN:/i.test(raw)));

  if (isDigiKey) {
    const norm = raw.replace(new RegExp(RS, 'g'), GS).replace(/\r?\n/g, GS);
    norm.split(GS).forEach(field => {
      const f = strip(field);
      if (!f || f === '[)>' || f === '06' || f === '>') return;

      // Quantity: 30P is customer reference on newer labels — only treat as qty if purely numeric
      if      (/^30P\d+$/.test(f))  result.quantity        = parseInt(f.slice(3))  || 0;
      else if (/^Q\d/.test(f))      result.quantity        = parseInt(f.slice(1))  || 0;
      // Manufacturer part number
      else if (f.startsWith('1P'))  result.manufacturer_pn = f.slice(2);
      // Manufacturer / vendor name (1V or 4V) — NOT 4L which is Country of Origin
      else if (f.startsWith('1V') || f.startsWith('4V')) result.manufacturer = f.slice(2);
      // Description
      else if (f.startsWith('DESC:') || f.startsWith('12Z')) result.description = f.replace(/^DESC:|^12Z/, '');
      // DigiKey PN: P prefix (newer labels) has priority; K prefix (older labels) fallback
      // Only set if non-empty and not already set
      else if (f.startsWith('P') && f.length > 1 && !result.digikey_pn) result.digikey_pn = f.slice(1);
      else if (f.startsWith('K') && f.length > 1 && !result.digikey_pn) result.digikey_pn = f.slice(1);
      // 4L = Country of Origin — intentionally ignored
    });
  } else if (isTME) {
    raw.trim().split(/\s+/).forEach(tok => {
      if (/^https?:\/\//i.test(tok)) return;        // skip the tme.eu URL (it contains ':')
      const idx = tok.indexOf(':');
      if (idx === -1) return;
      const key = tok.slice(0, idx).toUpperCase();
      const value = tok.slice(idx + 1);
      if (!value) return;

      if      (key === 'QTY') result.quantity        = parseInt(value) || 0;
      else if (key === 'MPN') result.manufacturer_pn = value;   // manufacturer part number
      else if (key === 'MFR') result.manufacturer    = value;   // manufacturer name
      else if (key === 'PN')  result.digikey_pn      = value;   // TME order symbol (primary reference)
      // PO (purchase order) and any other keys are intentionally ignored
    });
    // If the label carried no TME order symbol, fall back to the MPN as the headline.
    if (!result.digikey_pn) result.digikey_pn = result.manufacturer_pn;
  } else {
    result.digikey_pn = raw.trim();
  }
  return result;
}
