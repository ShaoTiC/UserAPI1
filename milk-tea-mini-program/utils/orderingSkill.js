const { products, toppings } = require("./catalog");

const DEFAULT_ORDER = {
  productId: "classic",
  size: "medium",
  sweetness: "50",
  ice: "normal",
  temperature: "cold",
  toppingIds: [],
  quantity: 1
};

const productAliases = [
  { id: "brown_sugar", terms: ["brown sugar", "brown sugar boba", "signature"] },
  { id: "jasmine", terms: ["jasmine", "flower", "floral"] },
  { id: "taro", terms: ["taro", "purple"] },
  { id: "classic", terms: ["classic", "original", "black tea", "milk tea"] }
];

const sizeAliases = [
  { id: "large", terms: ["large", "big", "l size"] },
  { id: "medium", terms: ["medium", "regular", "m size"] },
  { id: "small", terms: ["small", "little", "s size"] }
];

const sweetnessAliases = [
  { id: "0", terms: ["no sugar", "0 sugar", "0%", "zero sugar", "unsweetened"] },
  { id: "30", terms: ["30", "30%", "less sugar", "light sugar"] },
  { id: "50", terms: ["50", "50%", "half sugar"] },
  { id: "70", terms: ["70", "70%"] },
  { id: "100", terms: ["full sugar", "100", "100%", "normal sugar"] }
];

const iceAliases = [
  { id: "none", terms: ["no ice", "without ice"] },
  { id: "less", terms: ["less ice", "light ice"] },
  { id: "normal", terms: ["normal ice", "regular ice"] }
];

const temperatureAliases = [
  { id: "hot", terms: ["hot", "warm"] },
  { id: "cold", terms: ["cold", "iced"] }
];

function normalize(value) {
  return String(value || "").trim().toLowerCase();
}

function matchAlias(text, aliases) {
  return aliases.find((entry) => entry.terms.some((term) => text.includes(term)));
}

function parseQuantity(text) {
  const cupMatch = text.match(/(\d+)\s*(cups?|x)/);
  if (cupMatch) {
    return Math.max(Number(cupMatch[1]), 1);
  }

  const prefixMatch = text.match(/x\s*(\d+)/);
  if (prefixMatch) {
    return Math.max(Number(prefixMatch[1]), 1);
  }

  return DEFAULT_ORDER.quantity;
}

function parseToppings(text) {
  return toppings
    .filter((topping) => {
      const plainName = topping.name.toLowerCase();
      const spacedId = topping.id.replace("_", " ");
      return text.includes(plainName) || text.includes(spacedId);
    })
    .map((topping) => topping.id);
}

function parseMilkTeaUtterance(input) {
  const text = normalize(input);
  const productMatch = matchAlias(text, productAliases);
  const sizeMatch = matchAlias(text, sizeAliases);
  const sweetnessMatch = matchAlias(text, sweetnessAliases);
  const iceMatch = matchAlias(text, iceAliases);
  const temperatureMatch = matchAlias(text, temperatureAliases);
  const toppingIds = parseToppings(text);

  const order = {
    ...DEFAULT_ORDER,
    productId: productMatch ? productMatch.id : DEFAULT_ORDER.productId,
    size: sizeMatch ? sizeMatch.id : DEFAULT_ORDER.size,
    sweetness: sweetnessMatch ? sweetnessMatch.id : DEFAULT_ORDER.sweetness,
    ice: iceMatch ? iceMatch.id : DEFAULT_ORDER.ice,
    temperature: temperatureMatch ? temperatureMatch.id : DEFAULT_ORDER.temperature,
    toppingIds,
    quantity: parseQuantity(text)
  };

  const filledSlots = [
    productMatch && "product",
    sizeMatch && "size",
    sweetnessMatch && "sweetness",
    iceMatch && "ice",
    temperatureMatch && "temperature",
    toppingIds.length > 0 && "toppings"
  ].filter(Boolean);

  return {
    intent: "ORDER_MILK_TEA",
    confidence: Math.min(0.45 + filledSlots.length * 0.09, 0.95),
    slots: order,
    filledSlots,
    productName: products.find((product) => product.id === order.productId).name
  };
}

module.exports = {
  DEFAULT_ORDER,
  parseMilkTeaUtterance
};
