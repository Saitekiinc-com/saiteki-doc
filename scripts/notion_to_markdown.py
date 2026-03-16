#!/usr/bin/env python3
"""
Notionページを既存のdocs/practices形式のMarkdownに変換するスクリプト

特徴:
- Notionページ1つに対して、見出し構造に応じて1ファイル以上を出力
- 既存の docs/practices/lv{n}/ 配下に出力（lv はNotionの設定で指定）
- 再帰取得・ページネーション対応
- ファイル名はページタイトルからスネークケースに自動変換

使い方:
  export NOTION_TOKEN="ntn_xxx..."
  python3 scripts/notion_to_markdown.py

ページを追加するには:
  PAGE_CONFIGS リストにページIDとlvを追加するだけ
"""

import os
import re
import time
import requests

NOTION_TOKEN    = os.environ["NOTION_TOKEN"]
NOTION_VERSION  = "2022-06-28"
NOTION_BASE_URL = "https://api.notion.com/v1"

# リポジトリのdocsディレクトリ（このスクリプトからの相対パス）
DOCS_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "docs", "practices")

# 取得対象のNotionページ設定
# lv: 出力先のレベル（docs/practices/lv{n}/ に出力される）
# split_by_h2: Trueにするとh2ごとに別ファイルとして出力、Falseなら1ページ1ファイル
PAGE_CONFIGS = [
    {
        "page_id": "2fedfb42-679c-809e-921e-e2847839d2c7",
        "lv": 1,
        "split_by_h2": False,  # テスト観点抽出：1ファイルで出力
    },
    {
        "page_id": "30bdfb42-679c-802e-a6ab-ff11edaa2af9",
        "lv": 1,
        "split_by_h2": False,  # テスト戦略：1ファイルで出力
    },
    {
        "page_id": "30bdfb42-679c-80b6-99b4-f5bab3f42ad2",
        "lv": 1,
        "split_by_h2": False,  # テスト設計書作成：1ファイルで出力
    },
]


# =============================================
# Notion API
# =============================================

def notion_get(path: str, params: dict = None, retries: int = 3) -> dict:
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": NOTION_VERSION,
    }
    url = f"{NOTION_BASE_URL}{path}"
    for attempt in range(retries):
        resp = requests.get(url, headers=headers, params=params or {})
        if resp.status_code == 200:
            return resp.json()
        if resp.status_code in (502, 503, 429) and attempt < retries - 1:
            wait = 3 * (attempt + 1)
            print(f"  [{resp.status_code}] リトライ {attempt+1} ({wait}秒待機)...")
            time.sleep(wait)
        else:
            print(f"  [ERROR] {resp.status_code}: {resp.text[:100]}")
            return {}
    return {}


def get_page_title(page_id: str) -> str:
    data = notion_get(f"/pages/{page_id}")
    props = data.get("properties", {})
    title_prop = props.get("title", {})
    title_texts = title_prop.get("title", [])
    return "".join([t.get("plain_text", "") for t in title_texts])


def get_all_blocks(block_id: str, depth: int = 0) -> list:
    """ブロックを再帰的・ページネーション対応で全取得する"""
    blocks = []
    cursor = None

    while True:
        params = {"page_size": 100}
        if cursor:
            params["start_cursor"] = cursor

        data = notion_get(f"/blocks/{block_id}/children", params)
        if not data or "results" not in data:
            break

        for block in data["results"]:
            btype = block.get("type", "")
            block_data = block.get(btype, {})
            text = extract_plain_text(block_data)
            checked = block_data.get("checked", None)

            blocks.append({
                "type":         btype,
                "text":         text,
                "depth":        depth,
                "has_children": block.get("has_children", False),
                "block_id":     block["id"],
                "checked":      checked,
            })

            if block.get("has_children", False):
                children = get_all_blocks(block["id"], depth + 1)
                blocks.extend(children)

            time.sleep(0.03)

        if not data.get("has_more", False):
            break
        cursor = data.get("next_cursor")

    return blocks


def extract_plain_text(block_data: dict) -> str:
    rich_text = block_data.get("rich_text", [])
    parts = []
    for rt in rich_text:
        text = rt.get("plain_text", "")
        annotations = rt.get("annotations", {})
        if annotations.get("bold"):
            text = f"**{text}**"
        if annotations.get("code"):
            text = f"`{text}`"
        parts.append(text)
    return "".join(parts).strip()


# =============================================
# Markdown変換
# =============================================

BULLET_ICONS = {
    "human": "👤 **ユーザー (Human)**",
    "ai":    "🤖 **生成AI (AI)**",
}


def blocks_to_markdown(blocks: list) -> str:
    """ブロックリストをMarkdownテキストに変換する"""
    lines = []
    prev_type = None

    for block in blocks:
        btype = block["type"]
        text  = block["text"]
        depth = block["depth"]
        indent = "    " * depth

        if not text and btype not in ("divider",):
            # 空テキストは改行として扱う
            if prev_type not in ("", None):
                lines.append("")
            prev_type = ""
            continue

        if btype == "heading_1":
            lines.append(f"\n# {text}\n")
        elif btype == "heading_2":
            lines.append(f"\n## {text}\n")
        elif btype == "heading_3":
            lines.append(f"\n### {text}\n")
        elif btype == "heading_4":
            lines.append(f"\n#### {text}\n")
        elif btype == "bulleted_list_item":
            lines.append(f"{indent}- {text}")
        elif btype == "numbered_list_item":
            lines.append(f"{indent}1. {text}")
        elif btype == "to_do":
            mark = "x" if block.get("checked") else " "
            lines.append(f"{indent}- [{mark}] {text}")
        elif btype == "quote":
            lines.append(f"{indent}> {text}")
        elif btype == "code":
            lang = block.get("language", "")
            lines.append(f"```{lang}\n{text}\n```")
        elif btype == "divider":
            lines.append("\n---\n")
        elif btype == "callout":
            lines.append(f"\n> **{text}**\n")
        elif btype in ("paragraph", "text"):
            if text:
                lines.append(f"{indent}{text}")
            else:
                lines.append("")
        elif btype == "table_row":
            # テーブル行はcellsとして処理（簡易実装：テキストをそのまま）
            lines.append(f"| {text} |")
        else:
            if text:
                lines.append(f"{indent}{text}")

        prev_type = btype

    return "\n".join(lines)


def split_blocks_by_h2(title: str, blocks: list) -> list[tuple[str, list]]:
    """
    h2（heading_2）ごとにブロックを分割する
    Returns: [(セクション名, ブロックリスト), ...]
    """
    sections = []
    current_name = title
    current_blocks = []

    for block in blocks:
        if block["type"] == "heading_2" and block["depth"] == 0:
            if current_blocks:
                sections.append((current_name, current_blocks))
            current_name = block["text"]
            current_blocks = [block]
        else:
            current_blocks.append(block)

    if current_blocks:
        sections.append((current_name, current_blocks))

    return sections


def to_filename(text: str) -> str:
    """日本語タイトルをファイル名に変換する"""
    # 記号・スペースをアンダースコアに変換
    name = re.sub(r"[　\s/\\・〜～]+", "_", text)
    # 括弧・記号を除去
    name = re.sub(r"[「」『』【】（）()（）①②③④⑤⑥⑦⑧⑨\[\]<>《》]", "", name)
    # 先頭末尾のアンダースコアを除去
    name = name.strip("_")
    # 小文字化（英数字のみ）
    name = name.lower()
    # 連続アンダースコアを一つに
    name = re.sub(r"_+", "_", name)
    return name or "page"


def build_markdown(title: str, blocks: list) -> str:
    """ページタイトルとブロックリストからMarkdown全文を生成する"""
    content = blocks_to_markdown(blocks)

    return f"# {title}\n\n{content.strip()}\n"


# =============================================
# メイン処理
# =============================================

def main():
    print("=" * 50)
    print("Notion → Markdown 変換")
    print("=" * 50)

    generated_files = []

    for config in PAGE_CONFIGS:
        page_id     = config["page_id"]
        lv          = config["lv"]
        split_by_h2 = config.get("split_by_h2", False)

        print(f"\nページID: {page_id}")
        title = get_page_title(page_id)
        print(f"タイトル: {title}")

        print("ブロックを取得中...")
        blocks = get_all_blocks(page_id)
        print(f"取得完了: {len(blocks)}ブロック")

        # 出力ディレクトリ
        out_dir = os.path.join(DOCS_OUTPUT_DIR, f"lv{lv}")
        os.makedirs(out_dir, exist_ok=True)

        if split_by_h2:
            # h2ごとに別ファイルとして出力
            sections = split_blocks_by_h2(title, blocks)
            print(f"  {len(sections)}ファイルに分割して出力します")

            for section_name, section_blocks in sections:
                filename = to_filename(section_name) + ".md"
                filepath = os.path.join(out_dir, filename)
                md = build_markdown(section_name, section_blocks)

                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(md)
                print(f"  → {filepath.replace(os.path.dirname(DOCS_OUTPUT_DIR) + '/', '')}")
                generated_files.append(filepath)
        else:
            # 1ページ1ファイルで出力
            filename = to_filename(title) + ".md"
            filepath = os.path.join(out_dir, filename)
            md = build_markdown(title, blocks)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(md)
            print(f"  → {filepath.replace(os.path.dirname(DOCS_OUTPUT_DIR) + '/', '')}")
            generated_files.append(filepath)

    print(f"\n=== 完了: {len(generated_files)}ファイルを生成 ===")
    for f in generated_files:
        print(f"  {os.path.relpath(f)}")

    print("\n次のコマンドでGitHubにプッシュしてください:")
    print("  git add docs/practices/ && git commit -m 'docs: Notionからナレッジを更新' && git push")


if __name__ == "__main__":
    main()
