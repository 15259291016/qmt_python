from typing import List


class Solution:
    def canJump(self, nums: List[int]) -> bool:
        if nums[0]==len(nums):
            return True
        if len(nums) == 1:
            return True
        try:
            for i in nums:
                nums[i]
                if i + 1 >= len(nums):
                    return True
                if nums.index(i) + 2 == len(nums):
                    return True
        except Exception as e:
            return False

        return True
nums = [2,0,0]
import numpy as np

print(np.array(nums) * 2)
print([i * 2 for i in nums])
print(map(lambda i: i*2, nums))


# print(Solution().canJump(nums))
