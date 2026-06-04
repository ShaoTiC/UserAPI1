const {
  sizes,
  sweetnessLevels,
  iceLevels,
  temperatures,
  toppings,
  calculateOrder,
  formatMoney
} = require("../../utils/catalog");
const { DEFAULT_ORDER } = require("../../utils/orderingSkill");

const app = getApp();

Page({
  data: {
    order: { ...DEFAULT_ORDER },
    sizes,
    sweetnessLevels,
    iceLevels,
    temperatures,
    toppings,
    toppingsView: toppings,
    calculation: null,
    toppingSelection: {},
    notes: "",
    source: "menu"
  },

  onLoad(query) {
    const pendingOrder = app.globalData.pendingOrder || DEFAULT_ORDER;
    const normalizedOrder = {
      ...DEFAULT_ORDER,
      ...pendingOrder,
      toppingIds: pendingOrder.toppingIds || []
    };
    const toppingSelection = this.toToppingSelection(normalizedOrder.toppingIds);

    this.setData({
      order: normalizedOrder,
      toppingSelection,
      toppingsView: this.toToppingsView(toppingSelection),
      source: query.source || "menu"
    });
    this.refreshCalculation();
  },

  toToppingSelection(toppingIds) {
    return toppingIds.reduce((selection, toppingId) => {
      selection[toppingId] = true;
      return selection;
    }, {});
  },

  toToppingsView(toppingSelection) {
    return toppings.map((topping) => ({
      ...topping,
      selected: Boolean(toppingSelection[topping.id])
    }));
  },

  chooseOption(event) {
    const field = event.currentTarget.dataset.field;
    const value = event.currentTarget.dataset.value;

    this.setData({
      [`order.${field}`]: value
    });
    this.refreshCalculation();
  },

  toggleTopping(event) {
    const toppingId = event.currentTarget.dataset.id;
    const selected = {
      ...this.data.toppingSelection,
      [toppingId]: !this.data.toppingSelection[toppingId]
    };
    const toppingIds = Object.keys(selected).filter((id) => selected[id]);

    this.setData({
      toppingSelection: selected,
      toppingsView: this.toToppingsView(selected),
      "order.toppingIds": toppingIds
    });
    this.refreshCalculation();
  },

  changeQuantity(event) {
    const delta = Number(event.currentTarget.dataset.delta);
    const quantity = Math.max(1, this.data.order.quantity + delta);

    this.setData({
      "order.quantity": quantity
    });
    this.refreshCalculation();
  },

  onNotesInput(event) {
    this.setData({
      notes: event.detail.value
    });
  },

  refreshCalculation() {
    const calculation = calculateOrder(this.data.order);
    this.setData({
      calculation: {
        ...calculation,
        unitPriceText: formatMoney(calculation.unitPrice),
        lineTotalText: formatMoney(calculation.lineTotal)
      }
    });
  },

  addToCart() {
    const calculation = calculateOrder(this.data.order);
    const item = {
      id: `cart_${Date.now()}`,
      productId: calculation.product.id,
      productName: calculation.product.name,
      size: calculation.size.name,
      sweetness: calculation.sweetness.name,
      ice: calculation.ice.name,
      temperature: calculation.temperature.name,
      toppings: calculation.toppings.map((topping) => topping.name),
      toppingIds: calculation.toppings.map((topping) => topping.id),
      quantity: calculation.quantity,
      unitPrice: calculation.unitPrice,
      unitPriceText: formatMoney(calculation.unitPrice),
      lineTotal: calculation.lineTotal,
      lineTotalText: formatMoney(calculation.lineTotal),
      notes: this.data.notes.trim()
    };

    app.addToCart(item);
    app.globalData.pendingOrder = null;

    wx.showToast({
      title: "Added to cart",
      icon: "success"
    });

    wx.navigateTo({
      url: "/pages/cart/cart"
    });
  }
});
