from bisect import bisect_left


def longest_increasing_subsequence(nums):
    if not isinstance(nums, list) or any(type(x) is not int for x in nums):
        raise ValueError("nums must be a list of ints")
    tails = []
    for x in nums:
        i = bisect_left(tails, x)
        if i == len(tails):
            tails.append(x)
        else:
            tails[i] = x
    return len(tails)
