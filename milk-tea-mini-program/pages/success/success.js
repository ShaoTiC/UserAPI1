Page({
  data: {
    orderNo: "",
    cups: 0,
    total: "0.00"
  },

  onLoad(query) {
    this.setData({
      orderNo: query.orderNo || "MT-DEMO",
      cups: query.cups || 0,
      total: query.total || "0.00"
    });
  },

  backToMenu() {
    wx.reLaunch({
      url: "/pages/index/index"
    });
  }
});
