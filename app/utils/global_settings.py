"""PC est magique - Global settings"""

from app import db
from app.models import BarItem, GlobalSetting


class _SettingDescriptor:
    def __init__(self, key: str) -> None:
        self.key = key
        self.value: int = None  # Caching: only fetch attribute value on 1st access

    def __get__(self, obj: None, objtype=None):
        if self.value is None:
            self.value = GlobalSetting.query.filter_by(key=self.key).one().value
        return self.value

    def __set__(self, obj: None, value: int):
        if not isinstance(value, int):
            raise TypeError
        self.value = value
        setting = GlobalSetting.query.filter_by(key=self.key).one()
        setting.value = value
        db.session.commit()


class _QuickAccessItemDescriptor:
    def __get__(self, obj: None, objtype=None):
        return BarItem.query.get(Settings._quick_access_item_id)

    def __set__(self, obj: None, value: BarItem):
        if not isinstance(value, BarItem):
            raise TypeError
        Settings._quick_access_item_id = value.id


class Settings:
    max_daily_alcoholic_drinks_per_user: int = _SettingDescriptor("MAX_DAILY_ALCOHOLIC_DRINKS_PER_USER")
    _quick_access_item_id: int = _SettingDescriptor("QUICK_ACCESS_ITEM_ID")

    quick_access_item: BarItem = _QuickAccessItemDescriptor()
