const { formatMoney } = require("../../utils/catalog");

const app = getApp();

Page({
  data: {
    cart: [],
    totalText: "0.00",
    totalQuantity: 0
  },

  onShow() {
    this.refreshCart();
  },

  refreshCart() {
    const cart = app.globalData.cart;
    const total = cart.reduce((sum, item) => sum + item.lineTotal, 0);
    const totalQuantity = cart.reduce((sum, item) => sum + item.quantity, 0);
    const displayCart = cart.map((item) => ({
      ...item,
      toppingsText: item.toppings.join(", ")
    }));

    this.setData({
      cart: displayCart,
      totalText: formatMoney(total),
      totalQuantity
    });
  },

  removeItem(event) {
    app.removeFromCart(event.currentTarget.dataset.index);
    this.refreshCart();
  },

  clearCart() {
    app.clearCart();
    this.refreshCart();
  },

  continueOrdering() {
    wx.reLaunch({
      url: "/pages/index/index"
    });
  },

  checkout() {
    if (!this.data.cart.length) {
      wx.showToast({
        title: "Cart is empty",
        icon: "none"
      });
      return;
    }

    const orderNo = app.nextOrderNo();
    app.clearCart();

    wx.redirectTo({
      url: `/pages/success/success?orderNo=${orderNo}&cups=${this.data.totalQuantity}&total=${this.data.totalText}`
    });
  }
});
