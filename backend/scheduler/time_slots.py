"""
时间片定义
全周共 28 个时间片
- 周一至周四: 6节/天 (上午4节, 下午2节)
- 周五: 4节 (上午3节, 第4节为班会课)
"""

DAYS = ['周一', '周二', '周三', '周四', '周五']
DAY_CODES = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']

# 每天节数
PERIODS_PER_DAY = {
    0: 6,  # 周一
    1: 6,  # 周二
    2: 6,  # 周三
    3: 6,  # 周四
    4: 4,  # 周五
}

TOTAL_SLOTS = sum(PERIODS_PER_DAY.values())  # 28

# 上午节数 (0-3 为上午, 4-5 为下午)
AM_PERIODS = 4

# 特殊时段
FRIDAY_CLASS_MEETING = (4, 3)  # (day=周五, period=第4节)

# 合班课时段: 周二下午、周四下午
COMBINED_CLASS_SLOTS = [
    (1, 4), (1, 5),  # 周二下午
    (3, 4), (3, 5),  # 周四下午
]

# 连堂课禁止跨越的节次对 (period索引)
# 第2节(period=1)和第3节(period=2)之间有课间操，不允许连堂
# 第4节(period=3)和第5节(period=4)之间有午休，不允许连堂
CONSECUTIVE_FORBIDDEN_PAIRS = [(1, 2), (3, 4)]


def is_am_slot(day: int, period: int) -> bool:
    """判断是否为上午时段"""
    return period < AM_PERIODS


def is_combined_class_slot(day: int, period: int) -> bool:
    """判断是否为合班课时段"""
    return (day, period) in COMBINED_CLASS_SLOTS


def is_friday_class_meeting(day: int, period: int) -> bool:
    """判断是否为周五班会时段"""
    return (day, period) == FRIDAY_CLASS_MEETING


def get_all_slots():
    """获取所有时间片列表 [(day, period), ...]"""
    slots = []
    for day in range(5):
        for period in range(PERIODS_PER_DAY[day]):
            slots.append((day, period))
    return slots


def slot_to_str(day: int, period: int) -> str:
    """时间片转字符串"""
    return f"{DAYS[day]} 第{period + 1}节"
