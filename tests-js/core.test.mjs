import test from 'node:test';
import assert from 'node:assert/strict';
import {
  calculateProfit, generateDraft, inventoryToCsv, normalizeInventory,
  normalizeItem, resolvePlatformSelection,
} from '../web/core.js';

const base = normalizeItem({
  id: 'item-1', name: 'ダイバーズウォッチ', brand: 'SEIKO', category: '腕時計',
  condition: 'やや傷や汚れあり', model: '要確認', price: 10000, cost: 3000,
  feeRate: 10, shippingCost: 750, platforms: ['mercari'],
});

test('draft generation is bounded and does not assert unknown facts', () => {
  const draft = generateDraft(base, 'mercari');
  assert.ok(draft.title.includes('SEIKO'));
  assert.ok(draft.title.length <= 40);
  assert.match(draft.description, /要確認/);
  assert.doesNotMatch(draft.description, /動作確認済み/);
});

test('Yahoo flea market selection requires confirmation and becomes exclusive', () => {
  const first = resolvePlatformSelection(['mercari', 'rakuma'], 'yahoo-fleamarket', true);
  assert.equal(first.requiresConfirmation, true);
  const exclusive = resolvePlatformSelection([], 'yahoo-fleamarket', true);
  assert.deepEqual(exclusive.selected, ['yahoo-fleamarket']);
  const leaveExclusive = resolvePlatformSelection(['yahoo-fleamarket'], 'mercari', true);
  assert.deepEqual(leaveExclusive.selected, ['mercari']);
  assert.equal(leaveExclusive.removedExclusive, true);
});

test('profit calculation includes fees, cost and shipping', () => {
  assert.deepEqual(calculateProfit(base), { sale: 10000, fee: 1000, cost: 3000, shippingCost: 750, profit: 5250 });
});

test('CSV is UTF-8 BOM prefixed and escapes Japanese text safely', () => {
  const csv = inventoryToCsv([{ ...base, name: '時計, "限定"' }]);
  assert.equal(csv.charCodeAt(0), 0xfeff);
  assert.match(csv, /"時計, ""限定"""/);
  assert.doesNotMatch(csv, /data:image/);
});

test('inventory normalization removes invalid photos and duplicate ids', () => {
  const normalized = normalizeInventory({ items: [
    { ...base, photos: [{ thumbnail: 'javascript:alert(1)' }] },
    { ...base, name: '最新版', status: 'unknown', platforms: ['mercari', 'bad'] },
  ] });
  assert.equal(normalized.length, 1);
  assert.equal(normalized[0].name, '最新版');
  assert.equal(normalized[0].status, 'draft');
  assert.deepEqual(normalized[0].platforms, ['mercari']);
  assert.deepEqual(normalized[0].photos, []);
});
