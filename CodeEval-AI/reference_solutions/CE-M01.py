def max_subarray_sum(nums):
    if not isinstance(nums, list) or not nums or any(type(x) is not int for x in nums):
        raise ValueError("nums must be a non-empty list of ints")
    best = cur = nums[0]
    for x in nums[1:]:
        cur = max(x, cur + x)
        best = max(best, cur)
    return best
