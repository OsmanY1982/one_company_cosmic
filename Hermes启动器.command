#!/Users/opc/.hermes/hermes-agent/venv/bin/python
"""Hermes 一键启动器 — 数字选模型 → 进聊天"""

import subprocess, json, yaml, sys, os
from pathlib import Path

CONFIG = Path.home() / ".hermes/config.yaml"
HERMES = Path.home() / ".local/bin/hermes"
OLLAMA_URL = "http://localhost:11434"


def get_ollama_models():
    try:
        r = subprocess.run(["curl", "-s", f"{OLLAMA_URL}/api/tags"],
                           capture_output=True, text=True, timeout=10)
        return [m["name"] for m in json.loads(r.stdout).get("models", [])]
    except:
        return []


def read_config():
    with open(CONFIG) as f:
        return yaml.safe_load(f)


def write_config(cfg):
    with open(CONFIG, "w") as f:
        yaml.dump(cfg, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


def apply_config(model, api_url, api_key):
    cfg = read_config()
    cfg["model"]["default"] = model
    cfg["model"]["base_url"] = api_url
    cfg["model"]["provider"] = "custom"
    cfg["model"]["context_length"] = 131072
    cfg.setdefault("providers", {})
    cfg["providers"]["local-ollama"] = {"base_url": api_url, "api_key": api_key}
    write_config(cfg)
    print(f"\n模型 → {model}")
    print(f"API  → {api_url}")
    print("=" * 50)


def main():
    local_models = get_ollama_models()
    if not local_models:
        print("未检测到 Ollama 模型，请先导入。")
        sys.exit(1)

    print("=" * 50)
    print("  Hermes 启动器")
    print("=" * 50)
    print("\n本地模型:")
    for i, m in enumerate(local_models, 1):
        print(f"  [{i}] {m}")
    print(f"  [0] 自定义模型/API")

    while True:
        choice = input(f"\n选模型 (1-{len(local_models)}，回车=1): ").strip()

        if not choice:
            apply_config(local_models[0], f"{OLLAMA_URL}/v1", "ollama")
            break
        elif choice == "0":
            model = input(f"模型名 (回车={local_models[0]}): ").strip() or local_models[0]
            api_url = input(f"API地址 (回车={OLLAMA_URL}/v1): ").strip() or f"{OLLAMA_URL}/v1"
            api_key = input("API Key (本地留空): ").strip() or "ollama"
            apply_config(model, api_url, api_key)
            break
        elif choice.isdigit() and 1 <= int(choice) <= len(local_models):
            apply_config(local_models[int(choice) - 1], f"{OLLAMA_URL}/v1", "ollama")
            break
        else:
            print(f"无效，请输入 1-{len(local_models)} 或 0")

    print("\n启动 Hermes 聊天...\n")
    os.chdir(Path.home())
    os.execvp(str(HERMES), [str(HERMES), "chat"])


if __name__ == "__main__":
    main()