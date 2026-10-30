"""Executed in a fresh subprocess for every test case. Reads JSON on stdin, writes one JSON line."""
import io
import json
import sys


def main():
    out = sys.stdout
    req = json.loads(sys.stdin.read())
    sys.stdout = io.StringIO()  # swallow prints from the submission

    def emit(obj):
        out.write(json.dumps(obj) + "\n")
        out.flush()

    def err(e):
        emit({"status": "error", "error_type": type(e).__name__, "message": str(e)[:300]})

    ns = {"__name__": "submission"}
    try:
        exec(compile(req["code"], "<submission>", "exec"), ns)
    except BaseException as e:
        return err(e)
    fn = ns.get(req["function"])
    if not callable(fn):
        return emit({"status": "error", "error_type": "MissingFunction",
                     "message": "function %r not defined" % req["function"]})
    try:
        res = None
        for _ in range(req.get("repeat", 1)):
            res = fn(*req["args"])
        json.dumps(res)
    except BaseException as e:
        return err(e)
    emit({"status": "ok", "result": res})


if __name__ == "__main__":
    main()
