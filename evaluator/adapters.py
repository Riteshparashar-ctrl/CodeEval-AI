"""Configurable model adapters. Uses only the standard library (urllib).

Adapters never fabricate output: if credentials are missing or a call fails, nothing is recorded.
"""
import json
import os
import re
import urllib.error
import urllib.request


class AdapterError(RuntimeError):
    pass


def build_prompt(task):
    fn = task["function"]
    ex = "\n".join(f"  {fn}({', '.join(json.dumps(a) for a in t['args'])}) -> {json.dumps(t['expected'])}"
                   for t in task["tests"] if t["kind"] == "basic")
    return (f"Solve the following task in Python 3.\n\nTitle: {task['title']}\n\n{task['description']}\n\n"
            f"Input format: {task['input_format']}\nExpected output: {task['expected_output']}\n\n"
            f"Examples:\n{ex}\n\nRequirements: define a function named `{fn}`; use only the standard "
            f"library; reply with a single ```python code block and nothing else.")


def extract_code(text):
    blocks = re.findall(r"```(?:python|py)?[ \t]*\n(.*?)```", text, re.S | re.I)
    return (max(blocks, key=len) if blocks else text).strip() + "\n"


def _post(url, headers, body, timeout=180):
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise AdapterError(f"HTTP {e.code} from {url}") from e
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
        raise AdapterError(f"request failed: {type(e).__name__}") from e


class _Base:
    def __init__(self, cfg):
        self.cfg = cfg
        self.name = cfg["name"]
        self.version = cfg.get("version", "")

    def available(self):
        return bool(os.environ.get(self.cfg.get("api_key_env", "")))

    def _key(self):
        return os.environ[self.cfg["api_key_env"]]


class OpenAICompatibleAdapter(_Base):
    def generate(self, prompt):
        body = {"model": self.cfg["model"], "messages": [{"role": "user", "content": prompt}]}
        if "temperature" in self.cfg:
            body["temperature"] = self.cfg["temperature"]
        r = _post(self.cfg["base_url"].rstrip("/") + "/chat/completions",
                  {"Content-Type": "application/json", "Authorization": f"Bearer {self._key()}"}, body)
        try:
            return r["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as e:
            raise AdapterError("unexpected response shape") from e


class AnthropicAdapter(_Base):
    def generate(self, prompt):
        body = {"model": self.cfg["model"], "max_tokens": self.cfg.get("max_tokens", 2048),
                "messages": [{"role": "user", "content": prompt}]}
        base = self.cfg.get("base_url", "https://api.anthropic.com").rstrip("/")
        r = _post(base + "/v1/messages", {"Content-Type": "application/json", "x-api-key": self._key(),
                                           "anthropic-version": "2023-06-01"}, body)
        try:
            return "".join(b.get("text", "") for b in r["content"] if b.get("type") == "text")
        except (KeyError, TypeError) as e:
            raise AdapterError("unexpected response shape") from e


ADAPTERS = {"openai_compatible": OpenAICompatibleAdapter, "anthropic": AnthropicAdapter}


def make_adapter(cfg):
    cls = ADAPTERS.get(cfg.get("adapter"))
    if cls is None:
        raise AdapterError(f"unknown adapter {cfg.get('adapter')!r}; choose from {sorted(ADAPTERS)}")
    return cls(cfg)
