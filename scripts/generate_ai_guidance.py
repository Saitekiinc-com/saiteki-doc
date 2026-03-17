#!/usr/bin/env python3
"""
GitHub issueが作成されたときに:
1. Neo4jからナレッジグラフ全体を取得（Graph RAG）
2. Geminiにissueと関連ページ名のリストを渡し、どれが関連するか特定させる（JSON形式）
3. 特定されたページのリンク・AI活用内容・プロンプト例をコードで組み立てる
4. GitHub issueにコメントを投稿する
"""

import json
import os
import re
import requests
import google.generativeai as genai

# =============================================
# 環境変数から設定を読み込む
# =============================================
GEMINI_API_KEY  = os.environ["GEMINI_API_KEY"]
NEO4J_URI       = os.environ["NEO4J_URI"]
NEO4J_USER      = os.environ["NEO4J_USER"]
NEO4J_PASSWORD  = os.environ["NEO4J_PASSWORD"]
GITHUB_TOKEN    = os.environ["GITHUB_TOKEN"]
ISSUE_NUMBER    = os.environ["ISSUE_NUMBER"]
ISSUE_TITLE     = os.environ.get("ISSUE_TITLE", "")
ISSUE_BODY      = os.environ.get("ISSUE_BODY", "")
REPO            = os.environ["REPO"]

DOCS_BASE_URL   = "https://saitekiinc-com.github.io/saiteki-doc"


def filepath_to_url(filepath: str) -> str:
    """例: practices/lv1/estimation.md → https://...saiteki-doc/practices/lv1/estimation.html"""
    path = filepath.replace("\\", "/")
    if "practices/" in path:
        path = path[path.index("practices/"):]
    return f"{DOCS_BASE_URL}/{path.replace('.md', '.html')}"


# =============================================
# Neo4j: ナレッジグラフ全体を取得
# =============================================

def fetch_knowledge_graph() -> list[dict]:
    """Neo4jから全ページのナレッジを取得して辞書リストとして返す"""
    query = """
    MATCH (p:MarkdownPage)-[:DEFINES]->(h:HumanTask)
    OPTIONAL MATCH (h)-[:REPLACEABLE_BY|PARTIALLY_BY]->(g:AIGuidance)-[:USES_ROLE]->(r:AIRole)
    RETURN
        p.title          AS page_title,
        p.lv             AS lv,
        p.filepath       AS filepath,
        h.replaceable    AS replaceable,
        g.ai_tasks       AS ai_tasks,
        g.prompt_template AS prompt_template,
        g.output_example AS output_example,
        r.name           AS ai_role
    ORDER BY p.lv, p.title
    """
    resp = requests.post(
        NEO4J_URI,
        headers={"Content-Type": "application/json"},
        json={"statement": query},
        auth=(NEO4J_USER, NEO4J_PASSWORD),
    )
    if resp.status_code not in (200, 201):
        print(f"Neo4j ERROR: {resp.status_code}")
        return []

    pages = []
    seen  = set()
    for row in resp.json().get("data", {}).get("values", []):
        page_title, lv, filepath, replaceable, ai_tasks, prompt_template, output_example, ai_role = row
        if page_title in seen:
            continue
        seen.add(page_title)
        pages.append({
            "page_title":      page_title,
            "lv":              lv,
            "doc_url":         filepath_to_url(filepath) if filepath else "",
            "replaceable":     replaceable or "",
            "ai_tasks":        ai_tasks if isinstance(ai_tasks, list) else [],
            "prompt_template": prompt_template or "",
            "output_example":  output_example or "",
            "ai_role":         ai_role or "",
        })
    return pages


# =============================================
# Gemini: 関連ページを特定（JSON形式で）
# =============================================

def identify_relevant_pages(
    issue_title: str,
    issue_body:  str,
    pages:       list[dict],
) -> list[str]:
    """
    issueの内容からどのページが関連するかをGeminiに特定させる。
    返り値: 関連するpage_titleのリスト（最大3件）
    """
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-2.0-flash")

    page_list = "\n".join([f"- {p['page_title']} (Lv{p['lv']})" for p in pages])

    prompt = f"""
以下のGitHub issueの内容を読んで、このissueのタスクに最も関連する社内ナレッジを選んでください。

## GitHub issue
タイトル: {issue_title}
本文: {issue_body[:600] if issue_body else "（なし）"}

## 社内ナレッジ一覧（ページ名）
{page_list}

## 指示
上記の一覧から、このissueのタスクに関連するページを最大3件選び、
以下のJSON配列形式のみで返してください。他のテキストは不要です。

例: ["工数見積もりの精緻化", "API仕様の先行確定"]
"""
    response = model.generate_content(prompt)
    text = response.text.strip()

    # JSON配列を抽出
    match = re.search(r'\[.*?\]', text, re.DOTALL)
    if not match:
        return []
    try:
        titles = json.loads(match.group())
        return [t for t in titles if isinstance(t, str)][:3]
    except json.JSONDecodeError:
        return []


# =============================================
# コメント本文をコードで組み立て
# =============================================

def build_comment(
    issue_title:     str,
    relevant_titles: list[str],
    pages:           list[dict],
) -> str:
    """
    特定されたページのリンク・AIタスク・プロンプト例を使ってコメントを組み立てる
    """
    page_map = {p["page_title"]: p for p in pages}
    level_label = {
        "full":       "✅ AIが全量担当",
        "partial":    "⚡ AIが補助・人が最終判断",
        "human_only": "👤 人が必須",
    }

    if not relevant_titles:
        return "ナレッジグラフに関連するガイドラインが見つかりませんでした。\n新しいナレッジを追加していきましょう！"

    lines = []
    for title in relevant_titles:
        page = page_map.get(title)
        if not page:
            continue

        label = level_label.get(page["replaceable"], "")
        lines.append(f"### [{title}]({page['doc_url']}) {label}")

        if page["ai_tasks"]:
            lines.append("\n**AIにやってもらえること:**")
            for t in page["ai_tasks"][:3]:
                lines.append(f"- {t}")

        if page["output_example"]:
            lines.append(f"\n**期待する成果物:** {page['output_example']}")

        if page["prompt_template"]:
            # プロンプトテンプレートの先頭1〜2行を抜粋
            snippet = page["prompt_template"].split("\n")[0][:120]
            lines.append(f"\n**AIへの指示例:**")
            lines.append(f"> {snippet}")

        lines.append("")  # 空行

    return "\n".join(lines)


# =============================================
# GitHub: issueにコメントを投稿
# =============================================

def post_github_comment(repo: str, issue_number: str, body: str):
    url  = f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments"
    resp = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        json={"body": body},
    )
    if resp.status_code == 201:
        print(f"コメントを投稿しました: {resp.json()['html_url']}")
    else:
        print(f"GitHub ERROR: {resp.status_code} {resp.text[:200]}")
        raise RuntimeError("コメント投稿に失敗しました")


# =============================================
# メイン処理
# =============================================

def main():
    print(f"issue #{ISSUE_NUMBER}: {ISSUE_TITLE}")

    # 1. Neo4jからナレッジグラフを取得
    print("ナレッジグラフを取得中...")
    pages = fetch_knowledge_graph()
    print(f"取得完了: {len(pages)}ページ")

    # 2. Geminiで関連ページを特定
    print("Geminiで関連ページを特定中...")
    relevant_titles = identify_relevant_pages(ISSUE_TITLE, ISSUE_BODY, pages)
    print(f"関連ページ: {relevant_titles}")

    # 3. コメント本文をコードで組み立て
    header  = "## 🤖 AI活用ガイダンス\n\n"
    header += "_issueの内容をもとに、社内ナレッジグラフから関連するガイドラインを自動で提案しています。_\n\n"

    body_text    = build_comment(ISSUE_TITLE, relevant_titles, pages)
    full_comment = header + body_text

    print("\n=== 生成されたコメント ===")
    print(full_comment)

    # 4. GitHubにコメントを投稿
    post_github_comment(REPO, ISSUE_NUMBER, full_comment)


if __name__ == "__main__":
    main()
