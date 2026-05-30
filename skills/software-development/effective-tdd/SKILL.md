---
name: effective-tdd
description: "Test-driven development done right — RED-GREEN-REFACTOR with detailed patterns for test naming, assertions, fixtures, and mocking."
version: 1.0.0
author: Hermes Agent (adapted from OpenHands effective_tdd)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [tdd, testing, pytest, test-driven-development, quality]
    related_skills: [test-driven-development, python-debugpy, requesting-code-review]
---

# Effective TDD

Write tests that actually help. Not tests for coverage metrics — tests that catch bugs, document behavior, and make refactoring safe.

## The Iron Law

```
NO CODE WITHOUT A FAILING TEST FIRST
```

## The Cycle: RED → GREEN → REFACTOR

### RED — Write a Failing Test
Write the smallest test that describes the behavior you want. Run it. It MUST fail.

```python
def test_empty_cart_has_zero_total():
    cart = Cart()
    assert cart.total() == 0
```

### GREEN — Make It Pass
Write the minimum code to pass the test. Don't over-engineer.

```python
class Cart:
    def total(self):
        return 0
```

### REFACTOR — Clean Up
Now improve the code while keeping tests green.

```python
class Cart:
    def __init__(self):
        self._items = []
    
    def total(self):
        return sum(item.price for item in self._items)
```

## Test Naming

**Format:** `test_<unit>_<expected_behavior>`

```python
# ❌ Bad — vague
def test_cart():
def test_works():
def test_1():

# ✅ Good — describes scenario and outcome
def test_empty_cart_has_zero_total():
def test_cart_with_items_sums_prices():
def test_remove_item_not_in_cart_raises_error():
```

## Test Structure: Arrange → Act → Assert

```python
def test_discount_applied_to_premium_users():
    # Arrange
    user = User(plan="premium")
    shopping_cart = Cart(items=[Item("book", 25.00), Item("pen", 5.00)])
    
    # Act
    total = checkout(user, shopping_cart)
    
    # Assert
    assert total == 27.00  # 10% discount on $30
```

## One Assertion Per Concept

```python
# ❌ Bad — multiple unrelated asserts
def test_user():
    user = User("alice")
    assert user.name == "alice"
    assert user.email == ""
    assert user.is_active is True
    assert len(user.permissions) == 0

# ✅ Better — separate tests per concept
def test_user_default_name():
    user = User("alice")
    assert user.name == "alice"

def test_user_default_is_active():
    user = User("alice")
    assert user.is_active is True

def test_user_default_no_permissions():
    user = User("alice")
    assert len(user.permissions) == 0
```

## Parametrize for Edge Cases

```python
import pytest

@pytest.mark.parametrize("input,expected", [
    ("", True),        # empty string
    ("   ", True),     # whitespace
    ("hello", False),  # normal text
    ("0", False),      # falsy string
])
def test_is_blank(input, expected):
    assert is_blank(input) == expected
```

## Fixtures for Setup

```python
@pytest.fixture
def premium_user():
    return User(plan="premium", active=True)

@pytest.fixture
def sample_cart():
    return Cart(items=[
        Item("book", 25.00),
        Item("pen", 5.00),
    ])

def test_premium_discount_applied(premium_user, sample_cart):
    total = checkout(premium_user, sample_cart)
    assert total == 27.00
```

## Mocking: Only Dependencies, Never the Unit Under Test

```python
from unittest.mock import patch, MagicMock

def test_send_welcome_email():
    # Mock the email service dependency
    with patch("app.email_service.send") as mock_send:
        register_user("alice@example.com")
        
        mock_send.assert_called_once_with(
            to="alice@example.com",
            subject="Welcome!"
        )
```

### What to Mock
- **External services** (email, payment APIs, file storage)
- **Time-dependent code** (use `freezegun`)
- **Random values** (for reproducibility)
- **Database calls** (for unit tests — use test DB for integration)

### What NOT to Mock
- The function/module you're testing
- Simple data classes/value objects
- Python built-ins

## Test Organization

```
tests/
├── unit/              # Fast, isolated, no I/O
│   ├── test_models.py
│   ├── test_utils.py
│   └── test_services.py
├── integration/       # Components working together
│   ├── test_api.py
│   └── test_database.py
├── e2e/               # Full user flows
│   └── test_checkout.py
└── conftest.py        # Shared fixtures
```

## Common Patterns

### Testing Exceptions

```python
def test_withdraw_insufficient_funds():
    account = Account(balance=50)
    
    with pytest.raises(InsufficientFundsError) as exc_info:
        account.withdraw(100)
    
    assert exc_info.value.requested == 100
    assert exc_info.value.available == 50
```

### Testing Async Code

```python
import pytest
import asyncio

@pytest.mark.asyncio
async def test_fetch_user():
    user = await fetch_user(user_id=1)
    assert user.name == "alice"
```

### Time-Dependent Tests

```python
from freezegun import freeze_time

@freeze_time("2024-01-15")
def test_subscription_expiry():
    sub = Subscription(duration_days=30)
    assert sub.expires_at == datetime(2024, 2, 14)
```

## Anti-Patterns to Avoid

```python
# ❌ Testing implementation details
def test_user_uses_internal_dict():
    user = User("alice")
    assert isinstance(user._data, dict)  # Who cares internally?

# ✅ Testing behavior
def test_user_returns_name():
    user = User("alice")
    assert user.get_name() == "alice"

# ❌ Over-mocked — test proves nothing
def test_process():
    with patch("module.A"), patch("module.B"), patch("module.C"):
        result = process()
        assert result  # Tests the mocks, not the code

# ❌ Test with no assertions
def test_create_user():
    user = User("alice")  # If it doesn't raise, it passes?!
```

## Tips

- **Keep tests fast** — unit tests should run in milliseconds
- **Keep tests independent** — test order shouldn't matter
- **Name tests clearly** — the name IS the documentation
- **One failure = one reason** — easier to debug
- **Delete dead tests** — tests that never fail add maintenance cost
