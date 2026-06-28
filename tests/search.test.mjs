// Node regression tests for static/search.js — run with: node tests/search.test.mjs
import assert from 'node:assert/strict';
import { filterComponents, SEARCH_FIELDS } from '../static/search.js';

const PARTS = [
  { id: 1, digikey_pn: 'RHM33.0AFCT-ND', manufacturer_pn: 'ESR18EZPF33R0', manufacturer: 'ROHM',  description: 'RES SMD 33 OHM',  location: 'Drawer A1' },
  { id: 2, digikey_pn: '296-1234-ND',    manufacturer_pn: 'SN74LS125AD',   manufacturer: 'TI',    description: 'Quad buffer',      location: 'Drawer B2' },
  { id: 3, digikey_pn: 'CAP-1',          manufacturer_pn: 'GRM033R61A104', manufacturer: 'Murata', description: 'CAP CER 0.1UF',    location: 'Bin 7' },
];

let passed = 0;
function test(name, fn) { fn(); passed++; console.log(`  ok - ${name}`); }

test('empty term returns the full list', () => {
  assert.equal(filterComponents(PARTS, '', 'all').length, 3);
  assert.equal(filterComponents(PARTS, '   ', 'digikey_pn').length, 3);
});

test('all-fields search matches across reference, mfr ref, description, manufacturer, location', () => {
  assert.deepEqual(filterComponents(PARTS, 'rohm', 'all').map(c => c.id), [1]);     // manufacturer
  assert.deepEqual(filterComponents(PARTS, 'buffer', 'all').map(c => c.id), [2]);   // description
  assert.deepEqual(filterComponents(PARTS, 'bin 7', 'all').map(c => c.id), [3]);    // location
});

test('field-scoped search only matches the chosen field', () => {
  // 'SN74LS125AD' is a manufacturer_pn on part 2; searching the Reference field must NOT match it
  assert.deepEqual(filterComponents(PARTS, 'SN74LS125AD', 'manufacturer_pn').map(c => c.id), [2]);
  assert.deepEqual(filterComponents(PARTS, 'SN74LS125AD', 'digikey_pn').map(c => c.id), []);
});

test('search is case-insensitive and substring-based', () => {
  assert.deepEqual(filterComponents(PARTS, 'res smd', 'description').map(c => c.id), [1]);
  assert.deepEqual(filterComponents(PARTS, 'DRAWER', 'location').map(c => c.id), [1, 2]);
});

test('null/missing field values do not throw', () => {
  const withNulls = [{ id: 9, digikey_pn: null, manufacturer_pn: undefined, description: 'ok', manufacturer: null, location: null }];
  assert.deepEqual(filterComponents(withNulls, 'ok', 'all').map(c => c.id), [9]);
  assert.equal(filterComponents(withNulls, 'nope', 'all').length, 0);
});

test('SEARCH_FIELDS exposes the expected targetable fields', () => {
  assert.deepEqual(SEARCH_FIELDS.map(f => f.key), ['all', 'digikey_pn', 'manufacturer_pn', 'description', 'manufacturer', 'location']);
});

console.log(`\n${passed} search tests passed.`);
