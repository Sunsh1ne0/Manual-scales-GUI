
import datetime

try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo  import ZoneInfo

tz = ZoneInfo("Europe/Moscow")

# for zone in zoneinfo.available_timezones():
#     if "Reykjavik" in zone:

#         print(zone)