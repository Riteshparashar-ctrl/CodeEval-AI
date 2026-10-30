def is_palindrome(s):
    if not isinstance(s, str):
        raise ValueError("s must be a string")
    t = [c.lower() for c in s if c.isalnum()]
    return t == t[::-1]
