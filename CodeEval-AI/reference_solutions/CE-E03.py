def merge_sorted(a, b):
    for x in (a, b):
        if (not isinstance(x, list) or any(type(v) is not int for v in x)
                or any(x[i] > x[i + 1] for i in range(len(x) - 1))):
            raise ValueError("inputs must be ascending lists of ints")
    i = j = 0
    out = []
    while i < len(a) and j < len(b):
        if a[i] <= b[j]:
            out.append(a[i])
            i += 1
        else:
            out.append(b[j])
            j += 1
    out.extend(a[i:])
    out.extend(b[j:])
    return out
