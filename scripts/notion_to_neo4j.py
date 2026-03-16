#!/usr/bin/env python3
"""
Notion ページを完全取得してNeo4jナレッジグラフを生成するスクリプト

特徴:
- 子ブロックの再帰取得（has_children: true に対応）
- ページネーション対応（has_more: true に対応）
- ページIDを追加するだけで自動的にグラフに反映される設計
- Notionの「人の作業」「AIの作業」「AIにやってほしいこと」を正確に抽出

使い方:
  python3 notion_to_neo4j.py

ページを追加するには:
  PAGE_IDS リストにNotionのページIDを追加するだけ
"""

import requests
import json
import re
import time

# =============================================
# 設定
# =============================================

import os

# 環境変数から読み込む（.env ファイルまたはシェルで設定してから実行してください）
# 例:
#   export NOTION_TOKEN="ntn_xxxx..."
#   export NEO4J_PASSWORD="your-password"
NOTION_TOKEN    = os.environ["NOTION_TOKEN"]
NOTION_VERSION  = "2022-06-28"
NOTION_BASE_URL = "https://api.notion.com/v1"

NEO4J_URI      = os.environ.get("NEO4J_URI", "https://2ada646d.databases.neo4j.io/db/2ada646d/query/v2")
NEO4J_USER     = os.environ.get("NEO4J_USER", "2ada646d")
NEO4J_PASSWORD = os.environ["NEO4J_PASSWORD"]

# 取得対象のNotionページID（追加するときはここに足すだけ）
PAGE_IDS = [
    "2fedfb42-679c-809e-921e-e2847839d2c7",  # テスト観点抽出（汎用）
    "30bdfb42-679c-802e-a6ab-ff11edaa2af9",  # テスト戦略
    "30bdfb42-679c-80b6-99b4-f5bab3f42ad2",  # テスト設計書作成
]


# =============================================
# Notion API クライアント
# =============================================

def notion_get(path: str, params: dict = None, retries: int = 3) -> dict:
    """Notion API GETリクエスト（502エラー時は最大3回リトライ）"""
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
            wait_sec = 3 * (attempt + 1)
            print(f"  [Notion {resp.status_code}] リトライ {attempt+1}/{retries-1} ({wait_sec}秒待機)...")
            time.sleep(wait_sec)
        else:
            print(f"  [Notion ERROR] {resp.status_code}: {resp.text[:200]}")
            return {}
    return {}


def get_all_blocks(block_id: str, depth: int = 0) -> list:
    """
    ブロックの子を再帰的・ページネーション対応で全取得する
    Returns: テキスト情報のリスト（フラット化）
    """
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
            block_type = block.get("type", "")
            block_data = block.get(block_type, {})

            # テキストを抽出
            text = extract_text(block_data)
            if text:
                blocks.append({
                    "type": block_type,
                    "text": text,
                    "depth": depth,
                    "has_children": block.get("has_children", False),
                    "block_id": block["id"],
                })

            # 子ブロックを再帰取得
            if block.get("has_children", False):
                children = get_all_blocks(block["id"], depth + 1)
                blocks.extend(children)

            # APIレート制限対策
            time.sleep(0.05)

        if not data.get("has_more", False):
            break
        cursor = data.get("next_cursor")

    return blocks


def extract_text(block_data: dict) -> str:
    """ブロックデータからテキストを抽出する"""
    rich_text = block_data.get("rich_text", [])
    texts = []
    for rt in rich_text:
        plain = rt.get("plain_text", "")
        if plain:
            texts.append(plain)
    return " ".join(texts).strip()


def get_page_title(page_id: str) -> str:
    """ページのタイトルを取得する"""
    data = notion_get(f"/pages/{page_id}")
    props = data.get("properties", {})
    title_prop = props.get("title", {})
    title_texts = title_prop.get("title", [])
    return "".join([t.get("plain_text", "") for t in title_texts])


# =============================================
# Notionコンテンツの構造解析
# =============================================

def parse_page_content(blocks: list) -> dict:
    """
    ブロックリストからAI活用ナレッジを抽出する

    Notionページのパターン:
    - heading_2: セクション名（例：「① 情報構造化」「② システム特性抽出」）
    - heading_3: サブセクション（「人の作業」「AIの作業」「AIにやってほしいこと」「AI中間成果物」）
    - paragraph/bulleted_list_item: 具体的な内容

    Returns: {
        "sections": [
            {
                "name": "情報構造化",
                "human_tasks": [...],
                "ai_tasks": [...],
                "ai_requests": [...],
                "outputs": [...]
            }
        ]
    }
    """
    sections = []
    current_section = None
    current_subsection = None

    for block in blocks:
        text = block["text"].strip()
        btype = block["type"]
        depth = block["depth"]

        if not text:
            continue

        # 見出し2: 新しいセクション開始
        if btype == "heading_2" and depth == 0:
            # 番号と記号を除去してセクション名を取得
            clean_name = re.sub(r"^[①②③④⑤⑥⑦⑧⑨\d\.\s🎯]+", "", text).strip()
            clean_name = re.sub(r"フェーズ$", "", clean_name).strip()
            if clean_name:
                current_section = {
                    "name": clean_name,
                    "human_tasks": [],
                    "ai_tasks": [],
                    "ai_requests": [],
                    "outputs": [],
                }
                sections.append(current_section)
                current_subsection = None

        # 見出し3: サブセクション
        elif btype == "heading_3" and current_section is not None:
            current_subsection = text

        # 内容ブロック
        elif current_section is not None and current_subsection is not None:
            # 人の作業セクション
            if any(kw in current_subsection for kw in ["人の作業", "人がやること", "人が行う"]):
                if btype in ("bulleted_list_item", "numbered_list_item", "paragraph"):
                    if text and not text.startswith("AIに"):
                        current_section["human_tasks"].append(text)

            # AIの作業・AIにやってほしいことセクション
            elif any(kw in current_subsection for kw in ["AIの作業", "AIにやってほしいこと", "AIにお願い"]):
                if btype in ("bulleted_list_item", "numbered_list_item", "paragraph"):
                    if text and text not in ("AIにやってほしいこと", "AIにお願いしたいこと"):
                        current_section["ai_tasks"].append(text)

            # AI中間成果物・成果物セクション
            elif any(kw in current_subsection for kw in ["中間成果物", "AI成果物", "AI中間"]):
                if btype in ("bulleted_list_item", "numbered_list_item", "paragraph"):
                    if text:
                        current_section["outputs"].append(text)

    return {"sections": sections}


# =============================================
# Neo4j クライアント
# =============================================

def neo4j_run(query: str, params: dict = None):
    """Cypher クエリを実行する"""
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
# AI置き換え可能性の判定ロジック
# =============================================

def judge_replaceability(section_name: str, human_task: str, ai_tasks: list) -> tuple:
    """
    人の作業がAIで置き換えられるかを判定する

    Returns: (replaceable, replace_note)
    replaceable: "full" | "partial" | "human_only"
    """
    # AIの作業が定義されていない → 人必須
    if not ai_tasks:
        return "human_only", "AIの作業が定義されていないため人が必須"

    # 判定：人の作業とAIの作業の関係から判断
    # "ポリシー" "定義" "判断" "決定" "方針" は人必須 or partial
    human_judgment_keywords = ["ポリシー", "定義", "最終判断", "決定", "方針", "評価基準", "スコープ"]
    ai_can_do_keywords = ["列挙", "展開", "生成", "出力", "作成", "整形", "構造化", "候補", "ドラフト", "提案"]

    has_human_judgment = any(kw in human_task for kw in human_judgment_keywords)
    ai_can_replace = any(
        any(kw in ai_task for kw in ai_can_do_keywords) for ai_task in ai_tasks
    )

    if has_human_judgment:
        return "partial", f"「{human_task[:20]}」の最終判断は人が必須。AIはドラフト・候補出しを担当する"
    elif ai_can_replace:
        return "full", f"AIが「{'・'.join(ai_tasks[:2])}」を全量実施できる"
    else:
        return "partial", "人とAIが協働する作業"


def build_prompt_template(section_name: str, ai_tasks: list, outputs: list) -> str:
    """AIへの指示テンプレートを生成する"""
    ai_task_text = "\n".join([f"- {t}" for t in ai_tasks[:5]]) if ai_tasks else "- 内容を整理・展開する"
    output_text = outputs[0] if outputs else "整理された一覧"

    return (
        f"以下の情報をもとに「{section_name}」を実施してください。\n\n"
        f"【AIにお願いしたいこと】\n{ai_task_text}\n\n"
        f"【期待する出力】\n{output_text}\n\n"
        f"【インプット情報】\n{{{{input_text}}}}"
    )


# =============================================
# キーワードマッピング定義
# =============================================

SECTION_KEYWORDS = {
    "情報構造化": ["情報整理", "仕様書", "要件定義", "資料整理", "インプット整理"],
    "システム特性抽出": ["システム特性", "機能一覧", "特性", "アーキテクチャ"],
    "品質リスク抽出": ["品質リスク", "リスク洗い出し", "リスク抽出", "リスク", "不具合"],
    "リスク優先度決定": ["リスク優先度", "優先順位", "重要度", "リスク評価"],
    "テスト方針決定": ["テスト方針", "テスト戦略", "test strategy", "テスト計画"],
    "テスト体制設計": ["テスト体制", "体制設計", "テストチーム", "役割分担"],
    "観点抽出ポリシー定義": ["観点ポリシー", "抽出方針", "観点定義"],
    "観点展開": ["テスト観点", "観点抽出", "観点展開", "観点一覧", "観点洗い出し"],
    "精錬・アセット化": ["アセット化", "テンプレート化", "ナレッジ化"],
    "再利用テンプレート登録": ["テンプレート登録", "再利用", "ナレッジ登録"],
    "要求の構造化": ["要求整理", "要件整理", "仕様整理", "仕様", "要件", "要求"],
    "リスク特定": ["リスク特定", "リスク分析", "リスク", "bug", "バグ", "障害"],
    "テスト観点の生成": ["テスト観点", "観点生成", "観点", "テスト設計"],
    "テストケース自動生成": ["テストケース", "テスト項目", "テスト手順", "test case"],
    "ケースの削減・統合": ["ケース削減", "テスト削減", "統合"],
    "AIレビュー": ["レビュー", "review", "確認", "チェック", "検証"],
    "品質可視化": ["品質可視化", "カバレッジ", "network羅性", "ダッシュボード"],
}


# =============================================
# メイン処理
# =============================================

def main():
    print("=" * 50)
    print("Notion → Neo4j ナレッジグラフ生成")
    print("=" * 50)

    # Step 1: 全ページのコンテンツを取得
    print("\n[Step 1] Notionページの完全取得")
    all_page_data = []

    for page_id in PAGE_IDS:
        print(f"\n  ページID: {page_id}")
        title = get_page_title(page_id)
        print(f"  タイトル: {title}")

        print("  ブロックを再帰取得中（時間がかかります）...")
        blocks = get_all_blocks(page_id)
        print(f"  取得完了: {len(blocks)}ブロック")

        parsed = parse_page_content(blocks)
        print(f"  解析完了: {len(parsed['sections'])}セクション")
        for s in parsed["sections"]:
            print(f"    - {s['name']}: 人の作業{len(s['human_tasks'])}件 / AI作業{len(s['ai_tasks'])}件 / 成果物{len(s['outputs'])}件")

        all_page_data.append({
            "page_id": page_id,
            "title": title,
            "sections": parsed["sections"],
        })

    # 取得済みデータをJSONに保存（デバッグ用）
    with open("notion_data.json", "w", encoding="utf-8") as f:
        json.dump(all_page_data, f, ensure_ascii=False, indent=2)
    print("\n  → notion_data.json に保存しました")

    # Step 2: Neo4jをクリアして再構築
    print("\n[Step 2] Neo4jのクリア")
    neo4j_run("MATCH (n) DETACH DELETE n")
    print("  完了")

    # Step 3: ベースノードを作成
    print("\n[Step 3] ベースノードを作成")

    # AIRoleノード
    ai_roles = [
        ("role_expand",    "観点・候補展開",         "人間が見落としがちな観点・候補を網羅的に列挙する"),
        ("role_structure", "情報構造化",             "曖昧な情報をAIが処理しやすい構造に整形する"),
        ("role_draft",     "ドラフト生成",           "文書・コード・一覧のドラフトを高速に生成する"),
        ("role_review",    "レビュー・検証",         "抜け漏れ・整合性・品質をAIが確認する"),
        ("role_priority",  "優先度算出・推薦",       "条件を与えると優先度や推奨順を出力する"),
        ("role_classify",  "分類・タグ付け",         "テキストや項目を分類・カテゴライズする"),
        ("role_translate", "変換・トランスレーション","観点→ケースなど形式変換を行う"),
    ]
    for role_id, name, desc in ai_roles:
        neo4j_run(
            "CREATE (r:AIRole {id: $id, name: $name, description: $desc})",
            {"id": role_id, "name": name, "desc": desc},
        )
    print(f"  AIRole: {len(ai_roles)}件")

    # Conditionノード
    conditions = [
        ("cond_has_spec",    "仕様書・要件定義書がある"),
        ("cond_has_risk",    "リスク一覧がある"),
        ("cond_has_viewpoint","テスト観点が定義済み"),
        ("cond_external_api","外部API連携がある"),
        ("cond_async",       "非同期処理がある"),
        ("cond_data_change", "データ変更を伴う"),
        ("cond_new_feature", "新機能追加"),
        ("cond_past_bug",    "過去に障害あり"),
    ]
    for cond_id, name in conditions:
        neo4j_run(
            "CREATE (c:Condition {id: $id, name: $name})",
            {"id": cond_id, "name": name},
        )
    print(f"  Condition: {len(conditions)}件")

    # Step 4: ページごとにHumanTask・AIGuidanceを作成
    print("\n[Step 4] HumanTask・AIGuidanceを作成")

    # NotionPageノードを作成
    for page_data in all_page_data:
        neo4j_run(
            "CREATE (p:NotionPage {id: $id, title: $title})",
            {"id": page_data["page_id"], "title": page_data["title"]},
        )

    ht_count = 0
    ag_count = 0
    kw_count = 0

    for page_data in all_page_data:
        page_title = page_data["title"]
        print(f"\n  ページ: {page_title}")

        for section in page_data["sections"]:
            section_name = section["name"]
            human_tasks = section["human_tasks"]
            ai_tasks = section["ai_tasks"]
            outputs = section["outputs"]

            if not human_tasks and not ai_tasks:
                continue

            # 人の作業ごとにHumanTaskノードを作成
            human_task_text = " / ".join(human_tasks) if human_tasks else f"{section_name}を行う"
            replaceable, replace_note = judge_replaceability(section_name, human_task_text, ai_tasks)

            ht_id = f"ht_{page_data['page_id'][:8]}_{ht_count}"
            neo4j_run(
                """
                CREATE (h:HumanTask {
                    id: $id,
                    name: $name,
                    phase: $phase,
                    replaceable: $replaceable,
                    replace_note: $replace_note,
                    source_page: $source_page
                })
                """,
                {
                    "id": ht_id,
                    "name": section_name,
                    "phase": page_title,
                    "replaceable": replaceable,
                    "replace_note": replace_note,
                    "source_page": page_title,
                },
            )
            ht_count += 1

            # NotionPageとHumanTaskをリンク
            neo4j_run(
                """
                MATCH (p:NotionPage {id: $page_id}), (h:HumanTask {id: $ht_id})
                CREATE (p)-[:DEFINES]->(h)
                """,
                {"page_id": page_data["page_id"], "ht_id": ht_id},
            )

            # AIGuidanceノードを作成（AIタスクがある場合）
            if ai_tasks:
                ag_id = f"ag_{page_data['page_id'][:8]}_{ag_count}"
                prompt = build_prompt_template(section_name, ai_tasks, outputs)
                output_example = outputs[0] if outputs else f"{section_name}の成果物"

                neo4j_run(
                    """
                    CREATE (g:AIGuidance {
                        id: $id,
                        title: $title,
                        ai_tasks: $ai_tasks,
                        prompt_template: $prompt,
                        input_required: $input_required,
                        output_example: $output_example
                    })
                    """,
                    {
                        "id": ag_id,
                        "title": f"{section_name} - AI支援",
                        "ai_tasks": ai_tasks,
                        "prompt": prompt,
                        "input_required": "仕様書・直前ステップの成果物",
                        "output_example": output_example,
                    },
                )
                ag_count += 1

                # HumanTask → AIGuidanceのリンク
                rel_type = "REPLACEABLE_BY" if replaceable == "full" else "PARTIALLY_BY"
                neo4j_run(
                    f"""
                    MATCH (h:HumanTask {{id: $ht_id}}), (g:AIGuidance {{id: $ag_id}})
                    CREATE (h)-[:{rel_type}]->(g)
                    """,
                    {"ht_id": ht_id, "ag_id": ag_id},
                )

                # AIRoleを推定してリンク
                role_id = infer_ai_role(section_name, ai_tasks)
                neo4j_run(
                    """
                    MATCH (g:AIGuidance {id: $ag_id}), (r:AIRole {id: $role_id})
                    CREATE (g)-[:USES_ROLE]->(r)
                    """,
                    {"ag_id": ag_id, "role_id": role_id},
                )

            # DomainKeywordを作成してリンク
            keywords = SECTION_KEYWORDS.get(section_name, [section_name])
            for kw_text in keywords:
                kw_id = f"kw_{kw_text.replace(' ', '_').replace('・', '_')}"
                # キーワードが存在しなければ作成
                neo4j_run(
                    """
                    MERGE (k:DomainKeyword {id: $id})
                    ON CREATE SET k.word = $word
                    """,
                    {"id": kw_id, "word": kw_text},
                )
                neo4j_run(
                    """
                    MATCH (h:HumanTask {id: $ht_id}), (k:DomainKeyword {id: $kw_id})
                    MERGE (h)-[:TRIGGERED_BY]->(k)
                    """,
                    {"ht_id": ht_id, "kw_id": kw_id},
                )
                kw_count += 1

            print(f"    [{replaceable}] {section_name} → AI作業{len(ai_tasks)}件 / KW{len(keywords)}件")

    # Step 5: 投入結果の確認
    print("\n[Step 5] 投入結果")
    result = neo4j_run(
        "MATCH (n) RETURN labels(n)[0] AS label, count(n) AS cnt ORDER BY label"
    )
    if result and "data" in result:
        total = 0
        for row in result["data"]["values"]:
            print(f"  {row[0]}: {row[1]}件")
            total += row[1]
        print(f"  合計ノード: {total}件")

    rel_result = neo4j_run(
        "MATCH ()-[r]->() RETURN type(r) AS rel_type, count(r) AS cnt ORDER BY rel_type"
    )
    if rel_result and "data" in rel_result:
        print("\n  リレーション:")
        total_rel = 0
        for row in rel_result["data"]["values"]:
            print(f"    {row[0]}: {row[1]}件")
            total_rel += row[1]
        print(f"  合計リレーション: {total_rel}件")

    # Step 6: サンプル検索テスト
    print("\n[Step 6] サンプル検索: 「テスト観点」というissueの場合")
    sample = neo4j_run(
        """
        MATCH (k:DomainKeyword)<-[:TRIGGERED_BY]-(h:HumanTask)
        WHERE k.word CONTAINS 'テスト観点' OR k.word CONTAINS '観点'
        OPTIONAL MATCH (h)-[:REPLACEABLE_BY|PARTIALLY_BY]->(g:AIGuidance)
        RETURN h.name AS 作業, h.replaceable AS レベル, g.title AS AI支援, h.replace_note AS 備考
        LIMIT 5
        """
    )
    if sample and "data" in sample:
        for row in sample["data"]["values"]:
            print(f"  [{row[1]}] {row[0]}")
            if row[2]:
                print(f"         → {row[2]}")
            print(f"         備考: {row[3][:50] if row[3] else 'なし'}")

    print("\n=== 完了 ===")


def infer_ai_role(section_name: str, ai_tasks: list) -> str:
    """セクション名とAIタスクからAIRoleを推定する"""
    combined = section_name + " ".join(ai_tasks)
    if any(kw in combined for kw in ["列挙", "展開", "洗い出し", "候補"]):
        return "role_expand"
    if any(kw in combined for kw in ["整形", "構造化", "整理", "分類"]):
        return "role_structure"
    if any(kw in combined for kw in ["ドラフト", "生成", "作成"]):
        return "role_draft"
    if any(kw in combined for kw in ["レビュー", "確認", "チェック", "網羅"]):
        return "role_review"
    if any(kw in combined for kw in ["優先度", "スコア", "ランク"]):
        return "role_priority"
    if any(kw in combined for kw in ["変換", "トランスレーション", "ケース化"]):
        return "role_translate"
    return "role_expand"


if __name__ == "__main__":
    main()
