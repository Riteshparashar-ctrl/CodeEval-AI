def group_anagrams(words):
    if not isinstance(words, list) or any(not isinstance(w, str) for w in words):
        raise ValueError("words must be a list of strings")
    groups = {}
    for w in words:
        groups.setdefault("".join(sorted(w)), []).append(w)
    out = [sorted(g) for g in groups.values()]
    return sorted(out, key=lambda g: g[0])
