App({
  globalData: {
    cart: [],
    pendingOrder: null,
    orderSequence: 1000
  },

  addToCart(item) {
    this.globalData.cart.push(item);
  },

  removeFromCart(index) {
    this.globalData.cart.splice(index, 1);
  },

  clearCart() {
    this.globalData.cart = [];
  },

  nextOrderNo() {
    this.globalData.orderSequence += 1;
    return `MT${Date.now()}${this.globalData.orderSequence}`;
  }
});
