def second_largest(nums):
    if not isinstance(nums, list) or any(type(x) is not int for x in nums):
        raise ValueError("nums must be a list of ints")
    first = second = None
    for x in nums:
        if first is None or x > first:
            if first is not None:
                second = first
            first = x
        elif x != first and (second is None or x > second):
            second = x
    if second is None:
        raise ValueError("need at least two distinct values")
    return second
