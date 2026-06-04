# Milk Tea Ordering Skill Design

## 1. Goal

Design a mini-program skill that lets users order milk tea quickly, accurately, and pleasantly. The skill should support two ordering modes:

1. **Guided ordering**: users tap menu items and customize them step by step.
2. **Smart ordering**: users type a short natural-language request, and the skill fills the order form automatically.

The sample code implements both modes with local data and a rule-based parser.

## 2. Target users

- Office workers ordering quickly during breaks.
- Students who often reorder familiar drinks.
- New customers who need visual guidance and recommended combinations.
- Returning users who want personalization based on past preferences.

## 3. Core product ideas

### Fast order path

Users can start from menu cards, recommended presets, or text input. The flow minimizes required choices by using reasonable defaults:

- Medium size.
- 50% sugar.
- Normal ice.
- Cold temperature.
- No toppings unless selected or parsed.

### Smart slot filling

The skill extracts structured options from user text:

| Slot | Examples |
| --- | --- |
| Product | classic milk tea, jasmine milk tea, brown sugar boba |
| Size | small, medium, large |
| Sweetness | no sugar, 30%, 50%, 70%, full sugar |
| Ice | no ice, less ice, normal ice |
| Temperature | hot, cold |
| Toppings | boba, pudding, grass jelly, cheese foam |
| Quantity | 2 cups, x2 |

### Customization confirmation

Even when smart ordering fills options automatically, users land on the customization page to review and edit before adding to cart. This protects against parser mistakes and builds trust.

### Cart and checkout

The cart summarizes item names, options, toppings, quantity, and total price. Checkout produces a mock order number.

## 4. User journey

```text
Home
  -> Browse products
  -> Choose preset or type smart order
  -> Order customization
  -> Add to cart
  -> Cart review
  -> Checkout success
```

### Home page

- Shows brand story and menu cards.
- Provides smart order input.
- Shows common preset orders.

### Order page

- Shows selected drink.
- Lets user change size, sweetness, ice, temperature, toppings, quantity, and notes.
- Recalculates price instantly.

### Cart page

- Lists selected drinks.
- Supports remove and clear.
- Shows final total.

### Success page

- Displays order number and pickup guidance.
- Lets user return to the menu.

## 5. Skill architecture

```text
User input
  -> orderingSkill.parseMilkTeaUtterance()
  -> Structured slots
  -> app.globalData.pendingOrder
  -> Order page prefill
  -> User confirmation
  -> Cart
```

### Intent model

The demo focuses on one primary intent:

```json
{
  "intent": "ORDER_MILK_TEA",
  "confidence": 0.88,
  "slots": {
    "productId": "classic",
    "size": "large",
    "sweetness": "30%",
    "ice": "less",
    "temperature": "cold",
    "toppingIds": ["boba"],
    "quantity": 1
  }
}
```

Recommended production intents:

- `ORDER_MILK_TEA`: create a new drink order.
- `REORDER_LAST`: reorder the most recent order.
- `CUSTOMIZE_ITEM`: modify size, sugar, ice, or topping.
- `ADD_TOPPING`: add one or more toppings.
- `REMOVE_TOPPING`: remove toppings.
- `CHECK_CART`: inspect cart summary.
- `CHECKOUT`: submit order.
- `ASK_RECOMMENDATION`: request a recommendation.

## 6. Data model

### Product

```json
{
  "id": "classic",
  "name": "Classic Milk Tea",
  "description": "Black tea, fresh milk, and a smooth roasted finish.",
  "basePrice": 12.0,
  "tags": ["best seller", "creamy"]
}
```

### Cart item

```json
{
  "id": "order_1001",
  "productId": "classic",
  "productName": "Classic Milk Tea",
  "size": "medium",
  "sweetness": "50%",
  "ice": "normal",
  "temperature": "cold",
  "toppingIds": ["boba"],
  "quantity": 1,
  "unitPrice": 14.0,
  "lineTotal": 14.0
}
```

## 7. State design

| State | Description | Next state |
| --- | --- | --- |
| `idle` | Waiting on menu page | `collecting` |
| `collecting` | Parsing smart order or receiving taps | `confirming` |
| `confirming` | User reviews order options | `cart` |
| `cart` | User reviews all items | `checkout` or `idle` |
| `checkout` | Order submitted | `success` |
| `success` | Pickup guidance shown | `idle` |

## 8. Error and edge-case design

- Unknown product: default to Classic Milk Tea and ask user to confirm.
- Conflicting options: use the last recognized option and let the user edit.
- Missing required slots: apply defaults.
- Empty cart checkout: show a toast and keep the user on cart.
- Parser uncertainty: keep the text in notes or ask a follow-up in production.

## 9. Visual design direction

- Warm milk-tea palette: cream background, brown text, amber accent.
- Card-based layout for menu and options.
- Large tap targets for mobile use.
- Sticky action buttons for cart and checkout.

## 10. Production extension plan

### Backend

- Persist menu, inventory, orders, users, coupons, and store status.
- Validate price server-side.
- Integrate payment and pickup number generation.

### Personalization

- Save favorite drinks.
- Suggest recent orders.
- Remember default sugar and ice preferences.

### Advanced skill intelligence

- Replace rule-based parser with a cloud NLU service.
- Support multi-turn correction:
  - User: "I want jasmine milk tea."
  - Skill: "What sweetness?"
  - User: "30%, less ice, add pudding."
- Add recommendation logic based on weather, time, inventory, and user history.

### Operations

- Disable sold-out toppings.
- Show estimated pickup time.
- Add coupons, membership points, and store selection.

## 11. Validation checklist

- User can create an order from a menu card.
- User can create an order from smart text input.
- Parsed options prefill the customization page.
- Price updates when size, toppings, or quantity changes.
- Cart total matches item totals.
- Empty cart cannot checkout.
- Checkout success displays an order number.
