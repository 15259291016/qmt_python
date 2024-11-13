class Solution:
    def romanToInt(self, s: str) -> int:
        rm_dict = {
        'I':1,
        'IV':4,
        'V':5,
        'IX':9,
        'X':10,
        'XL':40,
        'L':50,
        'XC':90,
        'C':100,
        'CD':400,
        'D':500,
        'CM':900,
        'M':1000
        }
        s_w = ['IV', 'IX', 'XL', 'XC', 'CD', 'CM']
        res = 0
        index = len(s)
        while index > 0:
            if (s[index-2] + s[index-1]) in s_w:
                res += rm_dict[(s[index-2] + s[index-1])]
                index -= 1
            else:
                res += rm_dict[s[index-1]]
            index -= 1
        return res

s = "MCMXCIV"
print(Solution().romanToInt(s))
