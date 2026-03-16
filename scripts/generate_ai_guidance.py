#!/usr/bin/env python3
"""
GitHub issueが作成されたときに:
1. issueタイトル・本文のキーワードからNeo4jでHumanTaskを検索
2. 関連するAIGuidanceを取得
3. Gemini APIでコメント文を生成
4. GitHub issueにコメントを投稿する
"""

import os
import re
import requests
import google.generativeai as genai

# =============================================
# 環境変数から設定を読み込む
# =============================================
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
NEO4J_URI     = os.environ["NEO4J_URI"]
NEO4J_USER    = os.environ["NEO4J_USER"]
NEO4J_PASSWORD = os.environ["NEO4J_PASSWORD"]
GITHUB_TOKEN  = os.environ["GITHUB_TOKEN"]
ISSUE_NUMBER  = os.environ["ISSUE_NUMBER"]
ISSUE_TITLE   = os.environ.get("ISSUE_TITLE", "")
ISSUE_BODY    = os.environ.get("ISSUE_BODY", "")
REPO          = os.environ["REPO"]  # 例: Saitekiinc-com/saiteki-doc


# =============================================
# Neo4j: キーワードでHumanTaskとAIGuidanceを検索
# =============================================

def search_knowledge_graph(keywords: list[str]) -> list[dict]:
    """
    キーワードリストからNeo4jで関連するHumanTaskとAIGuidanceを取得する
    """
    if not keywords:
        return []

    # キーワードのOR条件でDomainKeywordを検索
    keyword_conditions = " OR ".join([
        f"toLower(k.word) CONTAINS toLower('{kw}')" for kw in keywords
    ])

    query = f"""
    MATCH (k:DomainKeyword)<-[:TRIGGERED_BY]-(h:HumanTask)
    WHERE {keyword_conditions}
    OPTIONAL MATCH (h)-[:REPLACEABLE_BY|PARTIALLY_BY]->(g:AIGuidance)-[:USES_ROLE]->(r:AIRole)
    RETURN
        h.name           AS task_name,
        h.replaceable    AS level,
        h.replace_note   AS note,
        h.source_page    AS source,
        g.title          AS guidance_title,
        g.ai_tasks       AS ai_tasks,
        g.prompt_template AS prompt_template,
        g.output_example  AS output_example,
        r.name           AS ai_role
    ORDER BY
        CASE h.replaceable WHEN 'full' THEN 1 WHEN 'partial' THEN 2 ELSE 3 END
    LIMIT 8
    """

    resp = requests.post(
        NEO4J_URI,
        headers={"Content-Type": "application/json"},
        json={"statement": query},
        auth=(NEO4J_USER, NEO4J_PASSWORD),
    )

    if resp.status_code not in (200, 201):
        print(f"Neo4j ERROR: {resp.status_code} {resp.text[:200]}")
        return []

    data = resp.json()
    results = []
    seen = set()

    for row in data.get("data", {}).get("values", []):
        task_name = row[0]
        if task_name in seen:
            continue
        seen.add(task_name)
        results.append({
            "task_name":      task_name,
            "level":          row[1],
            "note":           row[2],
            "source":         row[3],
            "guidance_title": row[4],
            "ai_tasks":       row[5] if isinstance(row[5], list) else [],
            "prompt_template":row[6],
            "output_example": row[7],
            "ai_role":        row[8],
        })

    return results


# =============================================
# キーワード抽出
# =============================================

def extract_keywords(title: str, body: str) -> list[str]:
    """
    issueタイトルと本文から検索キーワードを抽出する
    """
    text = f"{title} {body}"

    # テスト・品質関連キーワード
    pattern_keywords = [
        "テスト", "テスト戦略", "テスト設計", "テスト観点", "テストケース",
        "品質", "リスク", "観点", "カバレッジ", "レビュー",
        "仕様", "要件", "要求", "バグ", "不具合", "障害",
        "リファクタリング", "改修", "API", "パフォーマンス", "性能",
        "機能追加", "新機能", "設計", "実装",
    ]

    found = []
    for kw in pattern_keywords:
        if kw in text:
            found.append(kw)

    # タイトルの単語もキーワードとして追加（3文字以上の日本語・英数字）
    title_words = re.findall(r"[ぁ-んァ-ヶ一-龠A-Za-z0-9]{3,}", title)
    found.extend(title_words)

    return list(dict.fromkeys(found))  # 重複排除・順序維持


# =============================================
# Gemini: コメント文章を生成
# =============================================

def generate_comment(
    issue_title: str,
    issue_body: str,
    knowledge: list[dict],
) -> str:
    """
    Gemini APIでissueコメントを生成する
    """
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-2.0-flash")

    if not knowledge:
        # 関連ナレッジが見つからなかった場合
        prompt = f"""
あなたはソフトウェア開発チームのAI活用アドバイザーです。
以下のissueについて、AIを活用できる可能性があればアドバイスしてください。
関連するナレッジが見つからなかった場合でも、一般的なAI活用の観点でコメントしてください。

issueタイトル: {issue_title}
issue本文: {issue_body[:500]}

日本語で、Markdownで、200字程度で簡潔にコメントしてください。
"""
    else:
        # 知識グラフから関連情報が取得できた場合
        knowledge_text = ""
        for item in knowledge:
            level_label = {
                "full": "✅ AIが全量担当できる",
                "partial": "⚡ AIが補助・人が最終判断",
                "human_only": "👤 人が必須",
            }.get(item["level"], item["level"])

            knowledge_text += f"\n### {item['task_name']} [{level_label}]\n"
            knowledge_text += f"- 元ページ: {item['source']}\n"
            knowledge_text += f"- 判定理由: {item['note']}\n"

            if item["ai_tasks"]:
                ai_task_str = "\n  ".join(item["ai_tasks"][:4])
                knowledge_text += f"- AIがやること:\n  {ai_task_str}\n"

            if item["guidance_title"] and item["prompt_template"]:
                knowledge_text += f"- 推奨プロンプト: 「{item['guidance_title']}」テンプレートを使用\n"

        prompt = f"""
あなたはソフトウェア開発チームのAI活用アドバイザーです。
以下のGitHub issueに対して、AIを活用できる作業を社内ナレッジグラフから検索した結果をもとにコメントしてください。

## issueの概要
タイトル: {issue_title}
本文: {issue_body[:500] if issue_body else "（本文なし）"}

## 社内ナレッジグラフから取得した関連情報
{knowledge_text}

## コメント作成の指示
- 日本語で、Markdownフォーマットでコメントを作成してください
- 「このissueでAIに任せられる作業」を箇条書きで明示してください
- 「人が判断・決定する必要がある作業」も明示してください
- 実際に使えるAIへの指示例（プロンプトの雛形）を1つ含めてください
- ポジティブで実用的なトーンで書いてください
- 全体で400字以内にまとめてください
"""

    response = model.generate_content(prompt)
    return response.text


# =============================================
# GitHub: issueにコメントを投稿
# =============================================

def post_github_comment(repo: str, issue_number: str, body: str):
    """
    GitHub issueにコメントを投稿する
    """
    url = f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    payload = {"body": body}

    resp = requests.post(url, headers=headers, json=payload)
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

    # 1. キーワード抽出
    keywords = extract_keywords(ISSUE_TITLE, ISSUE_BODY)
    print(f"キーワード: {keywords}")

    # 2. ナレッジグラフを検索
    knowledge = search_knowledge_graph(keywords)
    print(f"関連ナレッジ: {len(knowledge)}件")
    for k in knowledge:
        print(f"  [{k['level']}] {k['task_name']}")

    # 3. コメント本文を生成
    header = "## 🤖 AI活用ガイダンス\n\n"
    header += "_このコメントはissue作成時に社内ナレッジグラフを参照して自動生成されました。_\n\n"

    body_text = generate_comment(ISSUE_TITLE, ISSUE_BODY, knowledge)
    full_comment = header + body_text

    print("\n=== 生成されたコメント ===")
    print(full_comment)

    # 4. GitHubにコメントを投稿
    post_github_comment(REPO, ISSUE_NUMBER, full_comment)


if __name__ == "__main__":
    main()
