def binary_search_first(nums, target):
    if not isinstance(nums, list):
        raise ValueError("nums must be a list")
    lo, hi = 0, len(nums)
    while lo < hi:
        mid = (lo + hi) // 2
        if nums[mid] < target:
            lo = mid + 1
        else:
            hi = mid
    return lo if lo < len(nums) and nums[lo] == target else -1
