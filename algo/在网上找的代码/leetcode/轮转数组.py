from typing import List


class Solution:
    def rotate(self, nums: List[int], k: int) -> None:
        """
        Do not return anything, modify nums in-place instead.
        """

        nums = nums[k+1:] + nums[:k+1]
        return nums
# nums = [-1,-100,3,99]
# k = 2
nums = [1,2,3,4,5,6,7]
k = 3
print(Solution().rotate(nums, k))
