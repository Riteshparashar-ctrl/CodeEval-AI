"""DEMO DATA ONLY. Synthetic, deliberately flawed submissions used to showcase the dashboard.

These are NOT outputs of any AI model. They are mutations of the reference solutions (or short naive
implementations) written by the project author. They are stored with is_demo=1 and always labelled DEMO.
"""
NAIVE_M01 = '''def max_subarray_sum(nums):
    if not isinstance(nums, list) or not nums:
        raise ValueError("bad")
    best = nums[0]
    for i in range(len(nums)):
        s = 0
        for j in range(i, len(nums)):
            s += nums[j]
            best = max(best, s)
    return best
'''
NAIVE_H01 = '''def longest_increasing_subsequence(nums):
    if not isinstance(nums, list):
        raise ValueError("bad")
    dp = [1] * len(nums)
    for i in range(len(nums)):
        for j in range(i):
            if nums[j] < nums[i]:
                dp[i] = max(dp[i], dp[j] + 1)
    return max(dp) if dp else 0
'''
NAIVE_H02 = '''def edit_distance(a, b):
    if not isinstance(a, str) or not isinstance(b, str):
        raise ValueError("bad")
    if not a:
        return len(b)
    if not b:
        return len(a)
    if a[0] == b[0]:
        return edit_distance(a[1:], b[1:])
    return 1 + min(edit_distance(a[1:], b), edit_distance(a, b[1:]), edit_distance(a[1:], b[1:]))
'''

# entry: (task_id, replacements | None, full_code | None). No replacements and no code = unmodified reference.
PROFILES = [
    {"model_name": "DEMO-A (mutated reference)", "model_version": "demo", "entries": [
        ("CE-E01", [("if second is None:", "if False:")], None),
        ("CE-E02", [("if c.isalnum()", "if c != ' '")], None),
        ("CE-E03", None, None), ("CE-M03", None, None), ("CE-H02", None, None),
        ("CE-M01", [("best = cur = nums[0]", "best = cur = 0")], None),
        ("CE-M02", [("return lo if lo < len(nums) and nums[lo] == target else -1",
                     "return lo if nums[lo] == target else -1")], None),
        ("CE-M04", [("return not stack", "return True")], None),
        ("CE-H01", [("bisect_left", "bisect_right")], None),
        ("CE-H03", [(" or n < 1", "")], None)]},
    {"model_name": "DEMO-B (naive algorithms)", "model_version": "demo", "entries": [
        ("CE-E03", None, None), ("CE-M01", None, NAIVE_M01), ("CE-H01", None, NAIVE_H01), ("CE-H02", None, NAIVE_H02)]},
]
