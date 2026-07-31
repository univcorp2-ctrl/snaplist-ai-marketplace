export const PLATFORM_META = Object.freeze({
  mercari: { label: 'メルカリ', tone: 'friendly' },
  'yahoo-auction': { label: 'Yahoo!オークション', tone: 'structured' },
  rakuma: { label: 'ラクマ', tone: 'friendly' },
  'yahoo-fleamarket': { label: 'Yahoo!フリマ', tone: 'concise', exclusive: true },
});

export const ITEM_STATUSES = Object.freeze(['draft', 'listed', 'sold', 'hold']);
const STATUS_SET = new Set(ITEM_STATUSES);
const PLATFORM_SET = new Set(Object.keys(PLATFORM_META));

const text = (value, fallback = '') => {
  const result = String(value ?? '').replace(/\s+/g, ' ').trim();
  return result || fallback;
};

const number = (value, fallback = 0) => {
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed >= 0 ? parsed : fallback;
};

const id = () => {
  if (globalThis.crypto?.randomUUID) return globalThis.crypto.randomUUID();
  return `item-${Date.now()}-${Math.random().toString(16).slice(2)}`;
};

const isoNow = () => new Date().toISOString();

export function normalizeItem(raw = {}) {
  const createdAt = text(raw.createdAt, isoNow());
  const platforms = Array.isArray(raw.platforms)
    ? [...new Set(raw.platforms.filter((platform) => PLATFORM_SET.has(platform)))]
    : ['mercari'];
  const photos = Array.isArray(raw.photos)
    ? raw.photos.slice(0, 4).map((photo, index) => ({
        id: text(photo?.id, `photo-${index}`),
        name: text(photo?.name, `photo-${index + 1}.jpg`),
        thumbnail: text(photo?.thumbnail).startsWith('data:image/') ? text(photo.thumbnail) : '',
      })).filter((photo) => photo.thumbnail)
    : [];

  return {
    id: text(raw.id, id()),
    createdAt,
    updatedAt: text(raw.updatedAt, createdAt),
    status: STATUS_SET.has(raw.status) ? raw.status : 'draft',
    source: raw.source === 'api' ? 'api' : 'demo',
    photos,
    name: text(raw.name),
    brand: text(raw.brand, '要確認'),
    category: text(raw.category, 'その他'),
    condition: text(raw.condition, '目立った傷や汚れなし'),
    color: text(raw.color),
    size: text(raw.size),
    model: text(raw.model, '要確認'),
    accessories: text(raw.accessories, '写真に写っているものがすべてです'),
    flaws: text(raw.flaws),
    shippingMethod: text(raw.shippingMethod, '追跡可能な方法'),
    shippingDays: text(raw.shippingDays, '2〜3日で発送'),
    price: Math.round(number(raw.price)),
    cost: Math.round(number(raw.cost)),
    feeRate: Math.min(100, number(raw.feeRate, 10)),
    shippingCost: Math.round(number(raw.shippingCost)),
    notes: text(raw.notes),
    platforms: platforms.length ? platforms : ['mercari'],
    drafts: typeof raw.drafts === 'object' && raw.drafts ? raw.drafts : {},
  };
}

export function normalizeInventory(input) {
  let source = input;
  if (typeof source === 'string') {
    try { source = JSON.parse(source); } catch { return []; }
  }
  const items = Array.isArray(source) ? source : Array.isArray(source?.items) ? source.items : [];
  const unique = new Map();
  items.map(normalizeItem).forEach((item) => unique.set(item.id, item));
  return [...unique.values()].sort((a, b) => b.updatedAt.localeCompare(a.updatedAt));
}

export function calculatePriceSuggestions(basePrice) {
  const base = Math.max(0, Math.round(number(basePrice)));
  const round100 = (value) => Math.max(0, Math.round(value / 100) * 100);
  return {
    quick: round100(base * 0.9),
    recommended: round100(base),
    premium: round100(base * 1.12),
  };
}

export function calculateProfit({ price, cost = 0, feeRate = 10, shippingCost = 0 }) {
  const sale = Math.round(number(price));
  const purchase = Math.round(number(cost));
  const shipping = Math.round(number(shippingCost));
  const rate = Math.min(100, number(feeRate, 10));
  const fee = Math.round(sale * rate / 100);
  return { sale, fee, cost: purchase, shippingCost: shipping, profit: sale - fee - purchase - shipping };
}

export function resolvePlatformSelection(selected, requested, checked) {
  const current = [...new Set((selected || []).filter((platform) => PLATFORM_SET.has(platform)))];
  if (!PLATFORM_SET.has(requested)) return { selected: current, requiresConfirmation: false };
  if (!checked) return { selected: current.filter((platform) => platform !== requested), requiresConfirmation: false };

  if (requested === 'yahoo-fleamarket') {
    const hasOther = current.some((platform) => platform !== 'yahoo-fleamarket');
    if (hasOther) return { selected: current, requiresConfirmation: true };
    return { selected: ['yahoo-fleamarket'], requiresConfirmation: false };
  }

  if (current.includes('yahoo-fleamarket')) {
    return { selected: [requested], requiresConfirmation: false, removedExclusive: true };
  }
  return { selected: [...new Set([...current, requested])], requiresConfirmation: false };
}

const conditionGuidance = (condition) => {
  if (condition.includes('新品') || condition.includes('未使用')) return '保管に伴うわずかな変化は写真でご確認ください。';
  if (condition.includes('傷') || condition.includes('汚れ')) return '傷や使用感は写真と説明をご確認のうえご検討ください。';
  return '中古品のため、細かな状態は写真でご確認ください。';
};

const titleFor = (item) => {
  const parts = [];
  if (item.brand && item.brand !== '要確認') parts.push(item.brand);
  parts.push(item.name || '商品名要確認');
  if (item.model && item.model !== '要確認') parts.push(item.model);
  if (item.color) parts.push(item.color);
  return parts.join(' ').replace(/\s+/g, ' ').trim().slice(0, 40);
};

export function generateDraft(rawItem, platform, variant = 0) {
  const item = normalizeItem(rawItem);
  const meta = PLATFORM_META[platform] || PLATFORM_META.mercari;
  const uncertain = !item.model || item.model === '要確認';
  const title = titleFor(item);
  const detailLines = [
    `商品名：${item.name || '要確認'}`,
    `ブランド：${item.brand || '要確認'}`,
    `カテゴリ：${item.category}`,
    `状態：${item.condition}`,
    item.color ? `カラー：${item.color}` : '',
    item.size ? `サイズ：${item.size}` : '',
    `型番：${item.model || '要確認'}`,
    `付属品：${item.accessories}`,
    item.flaws ? `傷・注意点：${item.flaws}` : '',
  ].filter(Boolean);
  const caution = `${conditionGuidance(item.condition)} ${uncertain ? '型番・真贋・動作は写真だけでは確定していないため、出品前に要確認です。' : '型番・真贋・動作は出品者が最終確認してください。'}`;
  const shipping = `${item.shippingMethod}で、${item.shippingDays}の予定です。`;
  const introVariants = {
    mercari: ['ご覧いただきありがとうございます。', '即購入歓迎です。商品情報をご確認ください。'],
    'yahoo-auction': ['【商品について】', '【出品内容】'],
    rakuma: ['ご覧いただきありがとうございます。丁寧に梱包して発送します。', 'プロフィール確認後、そのままご購入いただけます。'],
    'yahoo-fleamarket': ['商品情報をご確認ください。', '写真と説明をご確認のうえご購入ください。'],
  };
  const intros = introVariants[platform] || introVariants.mercari;
  const intro = intros[Math.abs(variant) % intros.length];
  let description;
  if (meta.tone === 'structured') {
    description = `${intro}\n${detailLines.join('\n')}\n\n【発送】\n${shipping}\n\n【ご確認ください】\n${caution}`;
  } else if (meta.tone === 'concise') {
    description = `${intro}\n\n${detailLines.join('\n')}\n\n${shipping}\n${caution}`;
  } else {
    description = `${intro}\n\n${item.name || '商品名要確認'}を出品します。\n\n${detailLines.join('\n')}\n\n${shipping}\n${caution}`;
  }
  return {
    platform,
    platformLabel: meta.label,
    title,
    description,
    price: item.price,
    condition: item.condition,
    shipping: `${item.shippingMethod} / ${item.shippingDays}`,
  };
}

export function draftAsText(draft) {
  return `${draft.title}\n\n${draft.description}\n\n価格：¥${Number(draft.price || 0).toLocaleString('ja-JP')}\n状態：${draft.condition}\n配送：${draft.shipping}`;
}

export function validateItem(rawItem) {
  const item = normalizeItem(rawItem);
  const errors = [];
  if (!item.name) errors.push('商品名を入力してください。');
  if (!item.condition) errors.push('状態を選択してください。');
  if (item.price <= 0) errors.push('販売価格を1円以上で入力してください。');
  return errors;
}

const exportable = (rawItem) => {
  const item = normalizeItem(rawItem);
  const { photos, ...safe } = item;
  return safe;
};

export function inventoryToJson(items) {
  return JSON.stringify({ version: 1, exportedAt: isoNow(), items: normalizeInventory(items).map(exportable) }, null, 2);
}

export function escapeCsvCell(value) {
  const cell = String(value ?? '');
  return /[",\r\n]/.test(cell) ? `"${cell.replaceAll('"', '""')}"` : cell;
}

export function inventoryToCsv(items) {
  const headers = ['id', 'status', 'name', 'brand', 'category', 'condition', 'model', 'price', 'cost', 'feeRate', 'shippingCost', 'platforms', 'updatedAt'];
  const rows = normalizeInventory(items).map((item) => [
    item.id, item.status, item.name, item.brand, item.category, item.condition, item.model,
    item.price, item.cost, item.feeRate, item.shippingCost, item.platforms.join('|'), item.updatedAt,
  ].map(escapeCsvCell).join(','));
  return `\ufeff${headers.join(',')}\r\n${rows.join('\r\n')}`;
}
