// Node regression tests for static/parser.js — run with: node tests/parser.test.mjs
// Covers DigiKey/Mouser, TME, and plain-barcode parsing.
import assert from 'node:assert/strict';
import { parseBarcode } from '../static/parser.js';

const GS = String.fromCharCode(29);
const RS = String.fromCharCode(30);
const EOT = String.fromCharCode(4);

let passed = 0;
function test(name, fn) {
  fn();
  passed++;
  console.log(`  ok - ${name}`);
}

// ── TME ─────────────────────────────────────────────────────────────────────
test('TME QR: extracts qty, MPN, manufacturer, and order symbol', () => {
  const raw = 'QTY:5 PN:SN74LS125AD MFR:TEXASINSTRUMENTS MPN:SN74LS125AD PO:7910976/3 HTTPS://WWW.TME.EU/DETAILS/SN74LS125AD';
  const r = parseBarcode(raw);
  assert.equal(r.quantity, 5);
  assert.equal(r.manufacturer_pn, 'SN74LS125AD');
  assert.equal(r.manufacturer, 'TEXASINSTRUMENTS');
  assert.equal(r.digikey_pn, 'SN74LS125AD');         // TME order symbol (PN)
  assert.equal(r.raw_barcode, raw);
});

test('TME QR: does not parse the tme.eu URL into a field', () => {
  const r = parseBarcode('QTY:1 MPN:RC0805FR-071KL MFR:YAGEO https://www.tme.eu/details/RC0805FR-071KL');
  assert.equal(r.digikey_pn, 'RC0805FR-071KL');      // falls back to MPN when no PN token
  assert.equal(r.manufacturer, 'YAGEO');
  assert.equal(r.quantity, 1);
  assert.ok(!/HTTPS|tme\.eu/i.test(r.manufacturer));
});

test('TME QR: distinct order symbol kept separate from MPN', () => {
  const r = parseBarcode('QTY:100 PN:RES-1K-0805 MFR:YAGEO MPN:RC0805FR-071KL https://www.tme.eu/details/RES-1K-0805');
  assert.equal(r.digikey_pn, 'RES-1K-0805');
  assert.equal(r.manufacturer_pn, 'RC0805FR-071KL');
  assert.equal(r.quantity, 100);
});

// ── DigiKey (regression) ─────────────────────────────────────────────────────
test('DigiKey Data Matrix: still parses PN, MPN, qty, manufacturer', () => {
  const raw = `[)>${RS}06${GS}PRHM33.0AFCT-ND${GS}1PESR18EZPF33R0${GS}30P454${GS}1VROHM${GS}${RS}${EOT}`;
  const r = parseBarcode(raw);
  assert.equal(r.digikey_pn, 'RHM33.0AFCT-ND');
  assert.equal(r.manufacturer_pn, 'ESR18EZPF33R0');
  assert.equal(r.quantity, 454);
  assert.equal(r.manufacturer, 'ROHM');
});

// ── Plain barcode (regression) ───────────────────────────────────────────────
test('Plain barcode: raw value becomes the part number', () => {
  const r = parseBarcode('0123456789');
  assert.equal(r.digikey_pn, '0123456789');
  assert.equal(r.manufacturer_pn, '');
});

console.log(`\n${passed} parser tests passed.`);
