"""PC est magique - Global settings"""

from app import db
from app.models import BarItem, GlobalSetting


class _SettingDescriptor:
    def __init__(self, key: str, default_value: int = None) -> None:
        self.key = key
        self.default_value = default_value
        self.value: int = None  # Caching: only fetch attribute value on 1st access

    def __get__(self, obj: None, objtype=None):
        if self.value is None:
            setting = GlobalSetting.query.filter_by(key=self.key).first()
            if setting:
                self.value = setting.value
            else:
                self.value = self.default_value
        return self.value

    def __set__(self, obj: None, value: int):
        if not isinstance(value, int):
            raise TypeError
        self.value = value
        setting = GlobalSetting.query.filter_by(key=self.key).first()
        if not setting:
            setting = GlobalSetting(key=self.key, value=value, name_fr=self.key, name_en=self.key)
            db.session.add(setting)
        else:
            setting.value = value
        db.session.commit()


class _QuickAccessItemDescriptor:
    def __get__(self, obj: None, objtype=None):
        return db.session.get(BarItem, Settings._quick_access_item_id)

    def __set__(self, obj: None, value: BarItem):
        if not isinstance(value, BarItem):
            raise TypeError
        Settings._quick_access_item_id = value.id


class _SettingsMeta:
    max_daily_alcoholic_drinks_per_user: int = _SettingDescriptor("MAX_DAILY_ALCOHOLIC_DRINKS_PER_USER")
    _quick_access_item_id: int = _SettingDescriptor("QUICK_ACCESS_ITEM_ID")

    quick_access_item: BarItem = _QuickAccessItemDescriptor()

    season_number_club_q: int = _SettingDescriptor("SEASON_NUMBER_CLUB_Q")
    bar_recharge_min: int = _SettingDescriptor("BAR_RECHARGE_MIN")
    bar_recharge_max: int = _SettingDescriptor("BAR_RECHARGE_MAX")
    carousel_autoplay_delay: int = _SettingDescriptor("CAROUSEL_AUTOPLAY_DELAY", default_value=8)


Settings = _SettingsMeta()
