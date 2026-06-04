const products = [
  {
    id: "classic",
    name: "Classic Milk Tea",
    description: "Black tea, fresh milk, and a smooth roasted finish.",
    basePrice: 12,
    tags: ["Best seller", "Creamy"]
  },
  {
    id: "jasmine",
    name: "Jasmine Milk Tea",
    description: "Floral jasmine tea with a clean milk finish.",
    basePrice: 13,
    tags: ["Light", "Fresh"]
  },
  {
    id: "brown_sugar",
    name: "Brown Sugar Boba",
    description: "Brown sugar syrup, milk, and warm chewy boba.",
    basePrice: 16,
    tags: ["Signature", "Sweet"]
  },
  {
    id: "taro",
    name: "Taro Milk Tea",
    description: "Velvety taro blended with milk tea.",
    basePrice: 15,
    tags: ["Rich", "Purple"]
  }
];

const sizes = [
  { id: "small", name: "Small", priceDelta: -2 },
  { id: "medium", name: "Medium", priceDelta: 0 },
  { id: "large", name: "Large", priceDelta: 3 }
];

const sweetnessLevels = [
  { id: "0", name: "No sugar" },
  { id: "30", name: "30%" },
  { id: "50", name: "50%" },
  { id: "70", name: "70%" },
  { id: "100", name: "Full sugar" }
];

const iceLevels = [
  { id: "none", name: "No ice" },
  { id: "less", name: "Less ice" },
  { id: "normal", name: "Normal ice" }
];

const temperatures = [
  { id: "cold", name: "Cold" },
  { id: "hot", name: "Hot" }
];

const toppings = [
  { id: "boba", name: "Boba", price: 2 },
  { id: "pudding", name: "Pudding", price: 2.5 },
  { id: "grass_jelly", name: "Grass Jelly", price: 2 },
  { id: "cheese_foam", name: "Cheese Foam", price: 3 }
];

const presets = [
  {
    id: "office_pick",
    name: "Office Pick",
    description: "Large classic milk tea, 30% sugar, less ice, boba.",
    order: {
      productId: "classic",
      size: "large",
      sweetness: "30",
      ice: "less",
      temperature: "cold",
      toppingIds: ["boba"],
      quantity: 1
    }
  },
  {
    id: "light_jasmine",
    name: "Light Jasmine",
    description: "Medium jasmine milk tea, no sugar, normal ice.",
    order: {
      productId: "jasmine",
      size: "medium",
      sweetness: "0",
      ice: "normal",
      temperature: "cold",
      toppingIds: [],
      quantity: 1
    }
  },
  {
    id: "warm_taro",
    name: "Warm Taro",
    description: "Hot taro milk tea, 50% sugar, pudding.",
    order: {
      productId: "taro",
      size: "medium",
      sweetness: "50",
      ice: "none",
      temperature: "hot",
      toppingIds: ["pudding"],
      quantity: 1
    }
  }
];

function findProduct(productId) {
  return products.find((product) => product.id === productId) || products[0];
}

function findSize(sizeId) {
  return sizes.find((size) => size.id === sizeId) || sizes[1];
}

function findSweetness(sweetnessId) {
  return sweetnessLevels.find((level) => level.id === sweetnessId) || sweetnessLevels[2];
}

function findIce(iceId) {
  return iceLevels.find((level) => level.id === iceId) || iceLevels[2];
}

function findTemperature(temperatureId) {
  return temperatures.find((temperature) => temperature.id === temperatureId) || temperatures[0];
}

function findTopping(toppingId) {
  return toppings.find((topping) => topping.id === toppingId);
}

function calculateOrder(order) {
  const product = findProduct(order.productId);
  const size = findSize(order.size);
  const selectedToppings = (order.toppingIds || [])
    .map(findTopping)
    .filter(Boolean);
  const toppingTotal = selectedToppings.reduce((total, topping) => total + topping.price, 0);
  const quantity = Math.max(Number(order.quantity) || 1, 1);
  const unitPrice = product.basePrice + size.priceDelta + toppingTotal;
  const lineTotal = unitPrice * quantity;

  return {
    product,
    size,
    sweetness: findSweetness(order.sweetness),
    ice: findIce(order.ice),
    temperature: findTemperature(order.temperature),
    toppings: selectedToppings,
    quantity,
    unitPrice,
    lineTotal
  };
}

function formatMoney(value) {
  return Number(value || 0).toFixed(2);
}

module.exports = {
  products,
  sizes,
  sweetnessLevels,
  iceLevels,
  temperatures,
  toppings,
  presets,
  findProduct,
  calculateOrder,
  formatMoney
};
