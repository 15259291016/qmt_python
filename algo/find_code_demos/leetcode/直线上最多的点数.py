from typing import List


class Solution:
    def maxPoints(self, points: List[List[int]]) -> int:
        n = len(points)
        if n < 2:
            return
        res = 2
        for i in range(n):
            x1, y1 = points[i][0], points[i][1]
            has = {}
            for j in range(i + 1, n):
                x2, y2 = points[j][0], points[j][1]
                if x1 == x2:
                    a, b, c = 1, 0, -x1
                elif y1 == y2:
                    a, b, c = 0, 1, -y1
                else:
                    a = 1.0
                    b = 1.0 * (x1 - x2) / (y2 - y1)
                    c = 1.0 * (x1 * y2 - x2 * y1) / (y1 - y2)
                if (a,b,c) in has.keys():
                    has[(a,b,c)] += 1
                    res = max(res,has[(a,b,c)])
                else:
                    has[(a,b,c)] = 2
        return res

print(Solution().maxPoints([[1,1],[3,2],[5,3],[4,1],[2,3],[1,4]]))
