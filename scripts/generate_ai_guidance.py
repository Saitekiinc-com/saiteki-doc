#!/usr/bin/env python3
"""
GitHub issueが作成されたときに:
1. Neo4jからナレッジグラフ全体を取得（Graph RAG）
2. Geminiでissueに関連するナレッジページを特定
3. 要件をもとにAI活用ロードマップをGeminiで生成
4. GitHub issueにコメントを投稿する
"""

import json
import os
import re
import requests
from google import genai
from google.genai import types

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
    path = filepath.replace("\\", "/")
    if "practices/" in path:
        path = path[path.index("practices/"):]
    return f"{DOCS_BASE_URL}/{path.replace('.md', '.html')}"


# =============================================
# Neo4j: ナレッジグラフ全体を取得
# =============================================

def fetch_knowledge_graph() -> list[dict]:
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
    if resp.status_code not in (200, 201, 202):
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
    client    = genai.Client(api_key=GEMINI_API_KEY)
    page_list = "\n".join([f"- {p['page_title']} (Lv{p['lv']})" for p in pages])

    prompt = f"""以下のGitHub issueに最も関連する社内ナレッジページを選んでください。

## GitHub issue
タイトル: {issue_title}
本文: {issue_body[:600] if issue_body else "（なし）"}

## 社内ナレッジ一覧
{page_list}

上記のリストから関連するページを最大3件選び、ページ名の配列をJSONで返してください。
"""
    print(f"ナレッジグラフから関連ページを特定中（{len(pages)}件から検索）...")
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
        ),
    )
    text = response.text.strip()
    print(f"Gemini応答: {text[:200]}")

    try:
        titles = json.loads(text)
        if isinstance(titles, list):
            cleaned = [re.sub(r'\s*\(Lv\d+\)\s*$', '', t).strip() for t in titles if isinstance(t, str)]
            return cleaned[:3]
        return []
    except json.JSONDecodeError:
        match = re.search(r'\[.*?\]', text, re.DOTALL)
        if not match:
            return []
        try:
            titles = json.loads(match.group())
            cleaned = [re.sub(r'\s*\(Lv\d+\)\s*$', '', t).strip() for t in titles if isinstance(t, str)]
            return cleaned[:3]
        except json.JSONDecodeError:
            return []


# =============================================
# 要件セクションをissue本文から抽出
# =============================================

def extract_requirements(body: str) -> str:
    """
    issueテンプレートの「要件」セクションを抽出する。
    テンプレート形式（## 要件）でも、フリーテキストでも対応。
    """
    if not body:
        return ""

    # テンプレート形式: "## 要件" または "### 要件" セクションを探す
    match = re.search(
        r'(?:^|\n)#{1,3}\s*要件\s*\n(.*?)(?=\n#{1,3}\s|\Z)',
        body,
        re.DOTALL | re.IGNORECASE,
    )
    if match:
        return match.group(1).strip()

    # フォールバック: 全文をそのまま返す
    return body.strip()


# =============================================
# Gemini: 要件ベースのロードマップを生成
# =============================================

def generate_roadmap(
    issue_title:     str,
    issue_body:      str,
    relevant_titles: list[str],
    pages:           list[dict],
) -> str:
    """
    要件と関連ナレッジをGeminiに渡してロードマップを生成する。
    """
    if not relevant_titles:
        return "関連するガイドラインが見つかりませんでした。新しいナレッジを追加していきましょう！"

    client   = genai.Client(api_key=GEMINI_API_KEY)
    page_map = {p["page_title"]: p for p in pages}

    # 関連ページの内容をコンテキストとして組み立てる
    knowledge_context = ""
    for title in relevant_titles:
        page = page_map.get(title)
        if not page:
            continue
        knowledge_context += f"\n### {title}\n"
        knowledge_context += f"ドキュメントURL: {page['doc_url']}\n"
        if page["ai_tasks"]:
            knowledge_context += "AIにできること:\n"
            for t in page["ai_tasks"][:3]:
                knowledge_context += f"  - {t}\n"
        if page["output_example"]:
            knowledge_context += f"期待する成果物: {page['output_example']}\n"

    requirements = extract_requirements(issue_body)

    prompt = f"""あなたはSaitekiのAI活用アドバイザーです。
以下の要件と社内ナレッジを参照して、このタスクを進めるためのAI活用ロードマップを作成してください。

## タスク
{issue_title}

## 要件
{requirements[:1000] if requirements else "（未記載）"}

## 利用できる社内ナレッジ
{knowledge_context}

## ロードマップの作成指示

以下の構成で、Markdownのロードマップを作成してください：

1. **方針（1〜2文）**: この要件に対してAIを使うにあたっての基本方針
2. **Step 1〜3（順序立てた手順）**: 各ステップで
   - 何をするか（タスク）
   - AIに何を任せるか
   - AIへの指示例（プロンプト1文）
   - 使える社内ナレッジへのMarkdownリンク
3. **人が判断・決定する必要があること**: 箇条書き1〜3件

日本語で、全体600字以内でまとめてください。ポジティブで実用的なトーンで書いてください。
"""

    print("要件ベースのロードマップを生成中...")
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
    )
    return response.text.strip()


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
    relevant_titles = identify_relevant_pages(ISSUE_TITLE, ISSUE_BODY, pages)
    print(f"関連ページ: {relevant_titles}")

    # 3. 要件をもとにロードマップを生成
    roadmap = generate_roadmap(ISSUE_TITLE, ISSUE_BODY, relevant_titles, pages)

    # 4. コメント本文を組み立て
    header  = "## 🤖 AI活用ロードマップ\n\n"
    header += "_issueの要件をもとに、社内ナレッジグラフからAI活用ロードマップを自動生成しました。_\n\n"
    header += "---\n\n"

    full_comment = header + roadmap

    print("\n=== 生成されたコメント ===")
    print(full_comment)

    # 5. GitHubにコメントを投稿
    post_github_comment(REPO, ISSUE_NUMBER, full_comment)


if __name__ == "__main__":
    main()
