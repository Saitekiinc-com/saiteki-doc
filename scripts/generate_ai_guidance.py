#!/usr/bin/env python3
"""
GitHub issueが作成されたときに:
1. Neo4jからナレッジグラフ全体を取得（Graph RAG）
2. issueとグラフコンテキストをGeminiに渡して意味的にマッチング
3. 関連するSaitekiドキュメントへのリンク・プロンプト例を含むコメントを生成
4. GitHub issueにコメントを投稿する
"""

import os
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
REPO            = os.environ["REPO"]  # 例: Saitekiinc-com/saiteki-doc

DOCS_BASE_URL   = "https://saitekiinc-com.github.io/saiteki-doc"


def filepath_to_url(filepath: str) -> str:
    """
    Neo4jのfilepathをGitHub PagesのURLに変換する
    例: practices/lv1/estimation.md → https://...saiteki-doc/practices/lv1/estimation.html
    """
    path = filepath.replace("\\", "/")
    # "practices/..." 以降だけ使う
    if "practices/" in path:
        path = path[path.index("practices/"):]
    html_path = path.replace(".md", ".html")
    return f"{DOCS_BASE_URL}/{html_path}"


# =============================================
# Neo4j: ナレッジグラフ全体を取得（Graph RAG）
# =============================================

def fetch_knowledge_graph() -> tuple[str, list[dict]]:
    """
    Neo4jからMarkdownPage → HumanTask → AIGuidance → AIRole
    のパスを全件取得し、Geminiに渡すコンテキストと生データを返す。
    """
    query = """
    MATCH (p:MarkdownPage)-[:DEFINES]->(h:HumanTask)
    OPTIONAL MATCH (h)-[:REPLACEABLE_BY|PARTIALLY_BY]->(g:AIGuidance)-[:USES_ROLE]->(r:AIRole)
    RETURN
        p.title          AS page_title,
        p.lv             AS lv,
        p.filepath       AS filepath,
        h.name           AS task_name,
        h.replaceable    AS replaceable,
        h.replace_note   AS replace_note,
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
        print(f"Neo4j ERROR: {resp.status_code} {resp.text[:200]}")
        return "", []

    data  = resp.json()
    rows  = data.get("data", {}).get("values", [])
    if not rows:
        return "", []

    raw_pages = []
    context_lines = ["## 社内ナレッジグラフ（Saitekiの作業とAI活用情報）\n"]
    current_page  = None

    for row in rows:
        page_title, lv, filepath, task_name, replaceable, replace_note, ai_tasks, prompt_template, output_example, ai_role = row

        doc_url = filepath_to_url(filepath) if filepath else ""

        if page_title != current_page:
            current_page = page_title
            context_lines.append(f"\n### [Lv{lv}] {page_title}")
            if doc_url:
                context_lines.append(f"ドキュメントURL: {doc_url}")

        level_label = {
            "full":       "✅ AIが全量担当できる",
            "partial":    "⚡ AIが補助・人が最終判断",
            "human_only": "👤 人が必須",
        }.get(replaceable, replaceable or "不明")

        context_lines.append(f"\n#### 作業: {task_name} [{level_label}]")
        if replace_note:
            context_lines.append(f"- 判定理由: {replace_note}")
        if ai_role:
            context_lines.append(f"- AIの役割: {ai_role}")
        if ai_tasks:
            tasks = ai_tasks if isinstance(ai_tasks, list) else [ai_tasks]
            context_lines.append("- AIがやること:")
            for t in tasks[:4]:
                context_lines.append(f"  - {t}")
        if output_example:
            context_lines.append(f"- 期待する成果物: {output_example}")

        raw_pages.append({
            "page_title":      page_title,
            "lv":              lv,
            "doc_url":         doc_url,
            "task_name":       task_name,
            "replaceable":     replaceable,
            "ai_tasks":        ai_tasks if isinstance(ai_tasks, list) else [],
            "prompt_template": prompt_template or "",
            "output_example":  output_example or "",
            "ai_role":         ai_role or "",
        })

    return "\n".join(context_lines), raw_pages


# =============================================
# Gemini: Graph RAGでコメント文章を生成
# =============================================

def generate_comment(
    issue_title:   str,
    issue_body:    str,
    graph_context: str,
) -> str:
    """
    Gemini APIにナレッジグラフ全体とissueを渡してコメントを生成する。
    """
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-2.0-flash")

    if not graph_context:
        prompt = f"""
あなたはSaitekiのAI活用アドバイザーです。
以下のGitHub issueについて、AIを活用できる可能性があればアドバイスしてください。

issueタイトル: {issue_title}
issue本文: {issue_body[:500]}

日本語で、Markdownで、200字程度で簡潔にコメントしてください。
"""
    else:
        prompt = f"""
あなたはSaitekiのAI活用アドバイザーです。
以下の「社内ナレッジグラフ」には、Saitekiが蓄積してきたAI活用のワークフロー情報が含まれています。

{graph_context}

---

## 対象のGitHub issue

タイトル: {issue_title}
本文:
{issue_body[:800] if issue_body else "（本文なし）"}

---

## コメント作成の指示

社内ナレッジグラフの中から、このissueに最も関連するページを特定して、以下の形式でコメントを作成してください。

**必ず守ること:**
1. 関連するガイドラインページを **最大3件** 選び、各ページについて以下を記述する
   - ページタイトルをMarkdownリンク形式で示す（ドキュメントURLを使う）
   - そのページで「AIに任せられる具体的な作業」を1〜2行で説明する
   - すぐ使えるプロンプト例を1文で示す（「AIへの指示例:」）
2. 最後に「人が判断・決定する必要がある作業」を箇条書きで1〜3件まとめる
3. 日本語のMarkdownで、全体500字以内にまとめる
4. ポジティブで実用的なトーンで書く
"""

    response = model.generate_content(prompt)
    return response.text


# =============================================
# GitHub: issueにコメントを投稿
# =============================================

def post_github_comment(repo: str, issue_number: str, body: str):
    url = f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    resp = requests.post(url, headers=headers, json={"body": body})
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

    # 1. Neo4jからナレッジグラフ全体を取得
    print("ナレッジグラフを取得中...")
    graph_context, raw_pages = fetch_knowledge_graph()
    print(f"取得完了: {len(raw_pages)}件のタスクノード")

    # 2. Graph RAGでコメント本文を生成
    print("Geminiでコメント生成中...")
    header  = "## 🤖 AI活用ガイダンス\n\n"
    header += "_issueの内容をもとに、社内ナレッジグラフから関連するガイドラインを自動で提案しています。_\n\n"

    body_text    = generate_comment(ISSUE_TITLE, ISSUE_BODY, graph_context)
    full_comment = header + body_text

    print("\n=== 生成されたコメント ===")
    print(full_comment)

    # 3. GitHubにコメントを投稿
    post_github_comment(REPO, ISSUE_NUMBER, full_comment)


if __name__ == "__main__":
    main()
