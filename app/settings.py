from sqlalchemy.orm import Session

from app.models import Setting

DEFAULT_CURRENCY = "INR"

CURRENCIES = {
    "INR": "₹",
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
    "JPY": "¥",
    "AUD": "A$",
    "CAD": "C$",
}


def get_currency(db: Session) -> str:
    setting = db.get(Setting, "currency")
    if setting and setting.value in CURRENCIES:
        return setting.value
    return DEFAULT_CURRENCY


def set_currency(db: Session, code: str) -> None:
    if code not in CURRENCIES:
        return
    setting = db.get(Setting, "currency")
    if setting:
        setting.value = code
    else:
        db.add(Setting(key="currency", value=code))
    db.commit()


def currency_symbol(code: str) -> str:
    return CURRENCIES.get(code, code)
