def n_queens_count(n):
    if type(n) is not int or n < 1:
        raise ValueError("n must be an int >= 1")
    cols, d1, d2 = set(), set(), set()

    def place(r):
        if r == n:
            return 1
        total = 0
        for c in range(n):
            if c in cols or (r - c) in d1 or (r + c) in d2:
                continue
            cols.add(c); d1.add(r - c); d2.add(r + c)
            total += place(r + 1)
            cols.remove(c); d1.remove(r - c); d2.remove(r + c)
        return total

    return place(0)
