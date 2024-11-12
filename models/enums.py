from enum import Enum

class RewardType(str, Enum):
    DISCOUNT_30 = "discount_30"  # 30% скидка за 1 друга
    DISCOUNT_40 = "discount_40"  # 40% скидка за 2 друзей
    DISCOUNT_50 = "discount_50"  # 50% скидка за 3 друзей