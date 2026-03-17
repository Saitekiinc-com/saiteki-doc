#!/usr/bin/env python3
"""
docs/practices/ 配下のMarkdownファイルを読み込んでNeo4jのナレッジグラフを生成するスクリプト

フロー:
  Notion → notion_to_markdown.py → docs/practices/**/*.md
                                          ↓ このスクリプト
                                       Neo4j ナレッジグラフ

使い方:
  export NEO4J_PASSWORD="your-password"
  python3 scripts/notion_to_neo4j.py

docs/practicesに新しいMarkdownを追加するだけで自動的にグラフに反映される
"""

import os
import re
import glob

import requests

NEO4J_URI      = os.environ.get("NEO4J_URI", "https://2ada646d.databases.neo4j.io/db/2ada646d/query/v2")
NEO4J_USER     = os.environ.get("NEO4J_USER", "2ada646d")
NEO4J_PASSWORD = os.environ["NEO4J_PASSWORD"]

# Markdownファイルの検索パス（このスクリプトからの相対パス）
DOCS_DIR = os.path.join(os.path.dirname(__file__), "..", "docs", "practices")

# AI活用に関係する見出しキーワード
HUMAN_TASK_HEADINGS = ["人がやること", "人の作業", "ユーザー", "Human"]
AI_TASK_HEADINGS    = ["AIの作業", "AIにやってほしいこと", "生成AI", "AI"]
OUTPUT_HEADINGS     = ["中間成果物", "AI成果物", "成果物", "Output"]



# =============================================
# Markdownパーサー
# =============================================

def parse_markdown_file(filepath: str) -> dict:
    """
    Markdownファイルを解析してナレッジ構造を抽出する

    Returns:
    {
        "title": "ページタイトル",
        "filepath": "相対パス",
        "lv": 1,
        "sections": [
            {
                "name": "セクション名",
                "human_tasks": ["..."],
                "ai_tasks": ["..."],
                "outputs": ["..."]
            }
        ]
    }
    """
    with open(filepath, encoding="utf-8") as f:
        lines = f.readlines()

    # lvをパスから取得
    lv = 1
    match = re.search(r"/lv(\d+)/", filepath.replace("\\", "/"))
    if match:
        lv = int(match.group(1))

    title = ""
    sections = []
    current_section = None
    current_subsection = None

    for line in lines:
        line_stripped = line.rstrip()

        # h1: ページタイトル
        if line_stripped.startswith("# ") and not line_stripped.startswith("## "):
            title = line_stripped[2:].strip()
            continue

        # h2: セクション（ステップ）の開始
        if line_stripped.startswith("## "):
            section_name = re.sub(r"^[①②③④⑤⑥⑦⑧⑨\d\.\s]+", "", line_stripped[3:]).strip()
            current_section = {
                "name":        section_name,
                "human_tasks": [],
                "ai_tasks":    [],
                "outputs":     [],
            }
            sections.append(current_section)
            current_subsection = None
            continue

        # h3: サブセクション（人の作業 / AIの作業 など）
        if line_stripped.startswith("### "):
            current_subsection = line_stripped[4:].strip()
            continue

        if current_section is None or current_subsection is None:
            continue

        # 箇条書き・本文を収集
        content = re.sub(r"^[-*]\s+", "", line_stripped).strip()
        # インデント箇条書きも対象
        content = re.sub(r"^\s+[-*]\s+", "", content).strip()
        if not content:
            continue

        # アイコン・絵文字を除去
        content = re.sub(r"^[👤🤖✅❌⭕■□◆◇●○▶▷※]\s*", "", content).strip()
        if not content:
            continue

        if any(kw in current_subsection for kw in HUMAN_TASK_HEADINGS):
            current_section["human_tasks"].append(content)
        elif any(kw in current_subsection for kw in AI_TASK_HEADINGS):
            current_section["ai_tasks"].append(content)
        elif any(kw in current_subsection for kw in OUTPUT_HEADINGS):
            current_section["outputs"].append(content)

    return {
        "title":    title or os.path.splitext(os.path.basename(filepath))[0],
        "filepath": os.path.relpath(filepath, os.path.dirname(DOCS_DIR)),
        "lv":       lv,
        "sections": sections,
    }


def judge_replaceability(human_tasks: list, ai_tasks: list) -> tuple[str, str]:
    """AI置き換え可能性を判定する"""
    if not ai_tasks:
        return "human_only", "AIの作業が定義されていないため人が必須"

    judgment_kws = ["ポリシー", "定義", "最終判断", "決定", "方針", "評価基準", "スコープ", "意思決定", "確定"]
    full_kws     = ["列挙", "展開", "生成", "出力", "作成", "整形", "構造化", "候補", "ドラフト", "提案"]

    human_text = " ".join(human_tasks)
    has_judgment = any(kw in human_text for kw in judgment_kws)

    if has_judgment:
        return "partial", f"人の意思決定が必要な箇所がある。AIはドラフト・候補出しを担当する"

    ai_text = " ".join(ai_tasks)
    if any(kw in ai_text for kw in full_kws):
        return "full", f"AIが網羅的に実施できる作業"

    return "partial", "人とAIが協働する作業"


def build_prompt_template(section_name: str, ai_tasks: list, outputs: list) -> str:
    task_text   = "\n".join([f"- {t}" for t in ai_tasks[:5]]) if ai_tasks else "- 内容を整理・展開する"
    output_text = outputs[0] if outputs else f"{section_name}の成果物"
    return (
        f"以下の情報をもとに「{section_name}」を実施してください。\n\n"
        f"【AIにお願いしたいこと】\n{task_text}\n\n"
        f"【期待する出力】\n{output_text}\n\n"
        f"【インプット情報】\n{{{{input_text}}}}"
    )


# =============================================
# Neo4j クライアント
# =============================================

def neo4j_run(query: str, params: dict = None):
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    payload = {"statement": query}
    if params:
        payload["parameters"] = params
    resp = requests.post(
        NEO4J_URI,
        headers=headers,
        json=payload,
        auth=(NEO4J_USER, NEO4J_PASSWORD),
    )
    if resp.status_code not in (200, 201, 202):
        print(f"  [Neo4j ERROR] {resp.status_code}: {resp.text[:200]}")
        return None
    return resp.json()


# =============================================
# Neo4jへの投入
# =============================================

AI_ROLES = [
    ("role_expand",    "観点・候補展開",          "人間が見落としがちな観点・候補を網羅的に列挙する"),
    ("role_structure", "情報構造化",              "曖昧な情報をAIが処理しやすい構造に整形する"),
    ("role_draft",     "ドラフト生成",            "文書・コード・一覧のドラフトを高速に生成する"),
    ("role_review",    "レビュー・検証",          "抜け漏れ・整合性・品質をAIが確認する"),
    ("role_priority",  "優先度算出・推薦",        "優先度や推奨順を出力する"),
    ("role_classify",  "分類・タグ付け",          "テキストや項目を分類・カテゴライズする"),
    ("role_translate", "変換・トランスレーション", "観点→ケースなど形式変換を行う"),
]

def infer_ai_role(section_name: str, ai_tasks: list) -> str:
    combined = section_name + " ".join(ai_tasks)
    if any(kw in combined for kw in ["列挙", "展開", "洗い出し", "候補", "抽出"]):
        return "role_expand"
    if any(kw in combined for kw in ["整形", "構造化", "整理"]):
        return "role_structure"
    if any(kw in combined for kw in ["ドラフト", "生成", "作成"]):
        return "role_draft"
    if any(kw in combined for kw in ["レビュー", "確認", "チェック", "網羅"]):
        return "role_review"
    if any(kw in combined for kw in ["優先度", "スコア"]):
        return "role_priority"
    if any(kw in combined for kw in ["変換", "ケース化"]):
        return "role_translate"
    return "role_expand"


def main():
    print("=" * 50)
    print("Markdown → Neo4j ナレッジグラフ生成")
    print("=" * 50)

    # Step 1: Markdownファイルを収集
    pattern = os.path.join(DOCS_DIR, "**", "*.md")
    md_files = sorted(glob.glob(pattern, recursive=True))
    print(f"\n[Step 1] Markdownファイルを検索")
    print(f"  {len(md_files)}ファイルを発見")
    for f in md_files:
        print(f"  - {os.path.relpath(f)}")

    # Step 2: Markdownを解析
    print("\n[Step 2] Markdownを解析")
    all_pages = []
    for filepath in md_files:
        page = parse_markdown_file(filepath)
        all_pages.append(page)
        active_sections = [s for s in page["sections"] if s["human_tasks"] or s["ai_tasks"]]
        print(f"  {page['title']}: セクション{len(page['sections'])}件（有効{len(active_sections)}件）")

    # Step 3: Neo4jをクリア
    print("\n[Step 3] Neo4jをクリア")
    neo4j_run("MATCH (n) DETACH DELETE n")
    print("  完了")

    # Step 4: ベースノードを作成
    print("\n[Step 4] ベースノードを作成")
    for role_id, name, desc in AI_ROLES:
        neo4j_run(
            "CREATE (r:AIRole {id: $id, name: $name, description: $desc})",
            {"id": role_id, "name": name, "desc": desc},
        )
    print(f"  AIRole: {len(AI_ROLES)}件")

    # Step 5: ページ・HumanTask・AIGuidanceを投入
    print("\n[Step 5] ナレッジを投入")
    ht_count = 0
    ag_count = 0

    for page in all_pages:
        # MarkdownPageノード
        neo4j_run(
            "CREATE (p:MarkdownPage {title: $title, filepath: $filepath, lv: $lv})",
            {"title": page["title"], "filepath": page["filepath"], "lv": page["lv"]},
        )

        print(f"\n  ページ: {page['title']} (lv{page['lv']})")

        for section in page["sections"]:
            human_tasks = section["human_tasks"]
            ai_tasks    = section["ai_tasks"]
            outputs     = section["outputs"]
            section_name = section["name"]

            if not human_tasks and not ai_tasks:
                continue

            replaceable, replace_note = judge_replaceability(human_tasks, ai_tasks)

            ht_id = f"ht_{ht_count}"
            neo4j_run(
                """
                CREATE (h:HumanTask {
                    id: $id, name: $name, phase: $phase,
                    replaceable: $replaceable, replace_note: $replace_note,
                    source_page: $source_page, source_file: $source_file
                })
                """,
                {
                    "id":           ht_id,
                    "name":         section_name,
                    "phase":        page["title"],
                    "replaceable":  replaceable,
                    "replace_note": replace_note,
                    "source_page":  page["title"],
                    "source_file":  page["filepath"],
                },
            )
            ht_count += 1

            neo4j_run(
                """
                MATCH (p:MarkdownPage {filepath: $fp}), (h:HumanTask {id: $ht_id})
                CREATE (p)-[:DEFINES]->(h)
                """,
                {"fp": page["filepath"], "ht_id": ht_id},
            )

            if ai_tasks:
                ag_id  = f"ag_{ag_count}"
                prompt = build_prompt_template(section_name, ai_tasks, outputs)
                output_example = outputs[0] if outputs else f"{section_name}の成果物"

                neo4j_run(
                    """
                    CREATE (g:AIGuidance {
                        id: $id, title: $title,
                        ai_tasks: $ai_tasks,
                        prompt_template: $prompt,
                        output_example: $output_example
                    })
                    """,
                    {
                        "id":            ag_id,
                        "title":         f"{section_name} - AI支援",
                        "ai_tasks":      ai_tasks,
                        "prompt":        prompt,
                        "output_example":output_example,
                    },
                )
                ag_count += 1

                rel = "REPLACEABLE_BY" if replaceable == "full" else "PARTIALLY_BY"
                neo4j_run(
                    f"MATCH (h:HumanTask {{id: $ht}}), (g:AIGuidance {{id: $ag}}) CREATE (h)-[:{rel}]->(g)",
                    {"ht": ht_id, "ag": ag_id},
                )

                role_id = infer_ai_role(section_name, ai_tasks)
                neo4j_run(
                    "MATCH (g:AIGuidance {id: $ag}), (r:AIRole {id: $role}) CREATE (g)-[:USES_ROLE]->(r)",
                    {"ag": ag_id, "role": role_id},
                )

            print(f"    [{replaceable}] {section_name} / 人:{len(human_tasks)} AI:{len(ai_tasks)}")

    # Step 6: 結果確認
    print("\n[Step 6] 投入結果")
    r = neo4j_run("MATCH (n) RETURN labels(n)[0] AS l, count(n) AS c ORDER BY l")
    total = 0
    for row in r["data"]["values"]:
        print(f"  {row[0]}: {row[1]}件")
        total += row[1]
    print(f"  合計ノード: {total}件")

    r2 = neo4j_run("MATCH ()-[r]->() RETURN type(r) AS t, count(r) AS c ORDER BY t")
    total_rel = 0
    for row in r2["data"]["values"]:
        print(f"  {row[0]}: {row[1]}件")
        total_rel += row[1]
    print(f"  合計リレーション: {total_rel}件")

    print("\n=== 完了 ===")


if __name__ == "__main__":
    main()
