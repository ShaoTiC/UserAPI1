const { products, presets } = require("../../utils/catalog");
const { parseMilkTeaUtterance } = require("../../utils/orderingSkill");

const app = getApp();

Page({
  data: {
    products,
    presets,
    smartText: "",
    parsedPreview: null
  },

  onInput(event) {
    this.setData({
      smartText: event.detail.value
    });
  },

  parseSmartOrder() {
    const smartText = this.data.smartText.trim();
    if (!smartText) {
      wx.showToast({
        title: "Type an order first",
        icon: "none"
      });
      return;
    }

    const parsed = parseMilkTeaUtterance(smartText);
    app.globalData.pendingOrder = parsed.slots;

    this.setData({
      parsedPreview: parsed
    });

    wx.navigateTo({
      url: "/pages/order/order?source=skill"
    });
  },

  startProductOrder(event) {
    const productId = event.currentTarget.dataset.id;
    app.globalData.pendingOrder = {
      productId,
      size: "medium",
      sweetness: "50",
      ice: "normal",
      temperature: "cold",
      toppingIds: [],
      quantity: 1
    };

    wx.navigateTo({
      url: "/pages/order/order?source=menu"
    });
  },

  startPreset(event) {
    const preset = this.data.presets.find((item) => item.id === event.currentTarget.dataset.id);
    if (!preset) {
      return;
    }

    app.globalData.pendingOrder = {
      ...preset.order
    };

    wx.navigateTo({
      url: "/pages/order/order?source=preset"
    });
  },

  openCart() {
    wx.navigateTo({
      url: "/pages/cart/cart"
    });
  }
});
