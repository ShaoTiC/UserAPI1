# Milk Tea Ordering Mini Program

This package is a complete design and code sample for a milk-tea ordering skill inside a WeChat-style mini-program. It includes:

- A product menu page.
- A smart ordering skill that parses simple natural-language requests.
- A customization page for size, sweetness, ice, temperature, toppings, and quantity.
- A cart page and checkout success page.
- Design documentation covering product thinking, interaction flow, data model, and extension ideas.

## How to run

1. Open WeChat DevTools.
2. Choose **Import Project**.
3. Select this `milk-tea-mini-program` folder.
4. Use the included `project.config.json`.
5. Compile and preview.

The demo does not require a backend. Cart data is stored in `app.globalData.cart` for local testing.

## Project structure

```text
milk-tea-mini-program/
  app.js
  app.json
  app.wxss
  project.config.json
  sitemap.json
  docs/
    design.md
  pages/
    index/
      index.js
      index.json
      index.wxml
      index.wxss
    order/
      order.js
      order.json
      order.wxml
      order.wxss
    cart/
      cart.js
      cart.json
      cart.wxml
      cart.wxss
    success/
      success.js
      success.json
      success.wxml
      success.wxss
  utils/
    catalog.js
    orderingSkill.js
```

## Skill examples

Try typing one of these requests on the home page:

- `large classic milk tea 30% sugar less ice boba`
- `jasmine milk tea no sugar hot pudding`
- `brown sugar boba medium normal ice`

The parser is intentionally lightweight and rule-based so it can run directly in the mini-program. In production, it can be replaced with a cloud function or LLM/NLU service while keeping the same slot model.
