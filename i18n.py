"""Locale registry and UI string catalogs for the Verifiable CDS demo.

The application is bilingual: Japanese (``ja``) is the default and English
(``en``) is selectable via a header toggle. Localization splits cleanly into
three buckets:

* :data:`UI_STRINGS` — every chrome string the templates render directly
  (header, sidebar, buttons, alerts, decoder legend).
* :data:`SCENARIOS_BY_LOCALE` (in :mod:`scenarios`) — the per-scenario
  natural-language metadata, including the *guidelines themselves*. The
  Japanese version cites Japanese clinical society guidelines (JSH, JSN,
  JDS, JSAD/JSNP, JRS); the English version cites the original American
  guidelines (AHA/ACC, KDIGO, ADA, AACE/ACE, APA, AASM).
* The Lean 4 source files in ``lean/`` are language-neutral — only the
  surrounding human-readable framing changes.

The locale code is resolved per-request from a ``?lang=`` query parameter
or a ``cds_lang`` cookie, with the query value winning so a deep link
overrides a previous toggle.
"""

from __future__ import annotations

from typing import Final

DEFAULT_LOCALE: Final[str] = "ja"
SUPPORTED_LOCALES: Final[tuple[str, ...]] = ("ja", "en")
LANGUAGE_COOKIE: Final[str] = "cds_lang"


def _r(kanji: str, reading: str) -> str:
    """Return an HTML ``<ruby>`` annotation for *kanji* with *reading*."""
    return f"<ruby>{kanji}<rp>(</rp><rt>{reading}</rt><rp>)</rp></ruby>"


def normalize_locale(value: str | None) -> str:
    """Return a supported locale code, falling back to :data:`DEFAULT_LOCALE`."""
    if value is None:
        return DEFAULT_LOCALE
    candidate = value.strip().lower()
    if candidate in SUPPORTED_LOCALES:
        return candidate
    return DEFAULT_LOCALE


# ---------------------------------------------------------------------------
# UI string catalogs.
# ---------------------------------------------------------------------------

UI_STRINGS: Final[dict[str, dict[str, str]]] = {
    "ja": {
        "html_lang": "ja",
        "page_title": (
            f"{_r('検証', 'けんしょう')}{_r('可能', 'かのう')}な"
            f"{_r('臨床', 'りんしょう')}{_r('意思', 'いし')}{_r('決定', 'けってい')}"
            f"{_r('支援', 'しえん')} ・ "
            f"{_r('認識論的', 'にんしきろんてき')}{_r('監査', 'かんさ')}"
        ),
        "brand_h1": (
            f"{_r('検証', 'けんしょう')}{_r('可能', 'かのう')}な"
            f"{_r('臨床', 'りんしょう')}{_r('意思', 'いし')}{_r('決定', 'けってい')}"
            f"{_r('支援', 'しえん')}"
        ),
        "brand_tagline": (
            f"{_r('認識論的', 'にんしきろんてき')}{_r('監査', 'かんさ')} ・ "
            f"ポリファーマシー{_r('衝突', 'しょうとつ')}の"
            f"{_r('形式', 'けいしき')}{_r('検証', 'けんしょう')}"
        ),
        "header_meta_pill": (
            f"ガイドライン{_r('衝突', 'しょうとつ')}の{_r('例', 'れい')}"
        ),
        "lang_switcher_label": f"{_r('言語', 'げんご')}",
        "lang_ja_label": f"{_r('日本語', 'にほんご')}",
        "lang_en_label": "English",
        "sidebar_title": f"{_r('臨床', 'りんしょう')}シナリオ",
        "sidebar_note": (
            f"{_r('各', 'かく')}シナリオは、{_r('単一', 'たんいつ')}の"
            f"{_r('患者', 'かんじゃ')}{_r('状況', 'じょうきょう')}において"
            f"{_r('推奨', 'すいしょう')}が{_r('衝突', 'しょうとつ')}する2つの"
            f"{_r('公開', 'こうかい')}{_r('臨床', 'りんしょう')}ガイドラインを"
            f"{_r('符号化', 'ふごうか')}しています。"
            f"{_r('形式', 'けいしき')}{_r('検証', 'けんしょう')}エンジンは、"
            f"{_r('符号化', 'ふごうか')}された{_r('公理', 'こうり')}から"
            f"{_r('論理的', 'ろんりてき')}{_r('矛盾', 'むじゅん')}を"
            f"{_r('導出', 'どうしゅつ')}することを{_r('試', 'こころ')}みます。"
        ),
        "copyright_affiliation": (
            f"{_r('北海道', 'ほっかいどう')}{_r('大学', 'だいがく')}"
            f"{_r('病院', 'びょういん')}"
        ),
        "status_pending": f"{_r('検証', 'けんしょう')}{_r('待', 'ま')}ち",
        "status_failed": f"{_r('検証', 'けんしょう')}{_r('失敗', 'しっぱい')}",
        "status_collision": (
            f"{_r('衝突', 'しょうとつ')}を{_r('検証', 'けんしょう')}"
            f"{_r('済', 'ず')}み"
        ),
        "status_unsound": f"{_r('証明', 'しょうめい')}が{_r('不健全', 'ふけんぜん')}",
        "status_rejected": f"Lean が{_r('証明', 'しょうめい')}を{_r('却下', 'きゃっか')}",
        "status_no_verdict": f"{_r('判定', 'はんてい')}なし",
        "patient_context_label": f"{_r('患者', 'かんじゃ')}{_r('背景', 'はいけい')}",
        "lean_mapping_label": "Lean マッピング",
        "legend_condition": f"{_r('病態', 'びょうたい')}",
        "legend_finding": f"{_r('所見', 'しょけん')}",
        "legend_intervention": f"{_r('介入', 'かいにゅう')}",
        "legend_indicated": f"{_r('適応', 'てきおう')}",
        "legend_contraindicated": f"{_r('禁忌', 'きんき')}",
        "guidelines_heading": f"{_r('臨床', 'りんしょう')}ガイドライン",
        "guideline_tag_a": "ガイドライン 1",
        "guideline_tag_b": "ガイドライン 2",
        "verify_button": (
            f"Lean {_r('形式', 'けいしき')}{_r('検証', 'けんしょう')}を"
            f"{_r('実行', 'じっこう')}"
        ),
        "verify_indicator": f"{_r('公理', 'こうり')}をコンパイル{_r('中', 'ちゅう')}…",
        "lean_heading": f"Lean 4 による{_r('形式化', 'けいしきか')}",
        "code_frame_hint_pre": f"{_r('下線', 'かせん')}{_r('付', 'つ')}きの",
        "code_frame_hint_demo": f"{_r('記号', 'きごう')}",
        "code_frame_hint_post": (
            f"には{_r('説明', 'せつめい')}のホバーがあります"
        ),
        "syntax_decoder_title": (
            f"この Lean {_r('証明', 'しょうめい')}の"
            f"{_r('読', 'よ')}み{_r('方', 'かた')}"
        ),
        "syntax_decoder_sub": (
            f"Lean やプログラミングの{_r('予備', 'よび')}{_r('知識', 'ちしき')}は"
            f"{_r('不要', 'ふよう')}です。{_r('以下', 'いか')}のグループは"
            f"{_r('簡単', 'かんたん')}な{_r('概要', 'がいよう')}であり、コード"
            f"{_r('中', 'ちゅう')}の{_r('下線', 'かせん')}{_r('付', 'つ')}きの"
        ),
        "syntax_decoder_sub_and": (
            f"や{_r('下線', 'かせん')}{_r('付', 'つ')}きの"
        ),
        "syntax_decoder_sub_demo_a": f"{_r('記号', 'きごう')}",
        "syntax_decoder_sub_demo_b": f"{_r('語句', 'ごく')}",
        "syntax_decoder_sub_post": (
            f"には、その{_r('行', 'ぎょう')}のために{_r('書', 'か')}かれた"
            f"ホバーツールチップが{_r('用意', 'ようい')}されて"
            f"います ── {_r('宣言', 'せんげん')}される{_r('名前', 'なまえ')}、"
            f"{_r('証明', 'しょうめい')}される{_r('主張', 'しゅちょう')}、"
            f"この{_r('患者', 'かんじゃ')}に{_r('適用', 'てきよう')}される"
            f"ガイドラインの{_r('公理', 'こうり')}など。"
        ),
        "decoder_group_structure": f"ファイル{_r('構造', 'こうぞう')}",
        "decoder_group_decls": f"{_r('宣言', 'せんげん')}",
        "decoder_group_tactics": f"{_r('証明', 'しょうめい')}{_r('戦術', 'せんじゅつ')}",
        "decoder_group_contradiction": f"{_r('矛盾', 'むじゅん')}",
        "decoder_dt_import": (
            f"{_r('別', 'べつ')}の Lean ファイルを{_r('読', 'よ')}み"
            f"{_r('込', 'こ')}む。ここでは{_r('共有', 'きょうゆう')}"
            f"{_r('医療', 'いりょう')}{_r('語彙', 'ごい')}。"
        ),
        "decoder_dt_namespace": (
            f"{_r('名前', 'なまえ')}{_r('付', 'つ')}きセクションを"
            f"{_r('開', 'ひら')}く。{_r('内部', 'ないぶ')}の"
            f"{_r('宣言', 'せんげん')}にはその{_r('接頭辞', 'せっとうじ')}が"
            f"{_r('付', 'つ')}く。"
        ),
        "decoder_dt_open": (
            f"{_r('接頭辞', 'せっとうじ')}を{_r('繰', 'く')}り"
            f"{_r('返', 'かえ')}さずに{_r('名前空間', 'なまえくうかん')}"
            f"{_r('内', 'ない')}の{_r('名前', 'なまえ')}を"
            f"{_r('参照', 'さんしょう')}する。"
        ),
        "decoder_dt_axiom": (
            f"Lean が{_r('証明', 'しょうめい')}なしに{_r('受', 'う')}け"
            f"{_r('入', 'い')}れる{_r('前提', 'ぜんてい')} ── "
            f"ガイドラインや{_r('患者', 'かんじゃ')}{_r('所見', 'しょけん')}。"
        ),
        "decoder_dt_theorem": (
            f"{_r('機械的', 'きかいてき')}に{_r('証明', 'しょうめい')}を"
            f"{_r('検査', 'けんさ')}した{_r('後', 'のち')}にのみ Lean が"
            f"{_r('受', 'う')}け{_r('入', 'い')}れる"
            f"{_r('主張', 'しゅちょう')}。"
        ),
        "decoder_dt_xt_label": "X : T",
        "decoder_dt_xt": (
            f"<code>:</code> は「は〜である」と{_r('読', 'よ')}む。"
            f"<code>«{_r('山田太郎', 'やまだたろう')}» : "
            f"«{_r('患者', 'かんじゃ')}»</code> = "
            f"「«{_r('山田太郎', 'やまだたろう')}» は "
            f"«{_r('患者', 'かんじゃ')}» である」。"
        ),
        "decoder_dt_xy_label": "X := Y",
        "decoder_dt_xy": (
            f"<code>:=</code> は「と{_r('定義', 'ていぎ')}する」と"
            f"{_r('読', 'よ')}む。{_r('右辺', 'うへん')}の"
            f"{_r('内容', 'ないよう')}に <code>X</code> という"
            f"{_r('名前', 'なまえ')}を{_r('与', 'あた')}える。"
        ),
        "decoder_dt_by": (
            f"ステップごとの{_r('戦術', 'せんじゅつ')}モードに"
            f"{_r('切', 'き')}り{_r('替', 'か')}える ── "
            f"{_r('証明', 'しょうめい')}を{_r('組', 'く')}み"
            f"{_r('立', 'た')}てるレシピ。"
        ),
        "decoder_dt_unfold": (
            f"「この{_r('名前', 'なまえ')}を{_r('定義', 'ていぎ')}で"
            f"{_r('置', 'お')}き{_r('換', 'か')}える」── その"
            f"{_r('構造', 'こうぞう')}を{_r('可視化', 'かしか')}する。"
        ),
        "decoder_dt_apply": (
            f"「この{_r('補題', 'ほだい')}を{_r('使', 'つか')}う。"
            f"{_r('前提', 'ぜんてい')}は{_r('次', 'つぎ')}に"
            f"{_r('証明', 'しょうめい')}する」と{_r('新', 'あたら')}しい"
            f"{_r('部分', 'ぶぶん')}{_r('目標', 'もくひょう')}として"
            f"{_r('展開', 'てんかい')}する。"
        ),
        "decoder_dt_exact": (
            f"「ここに{_r('示', 'しめ')}すのが{_r('必要', 'ひつよう')}な"
            f"{_r('証明', 'しょうめい')}そのもの ── このステップを"
            f"{_r('閉', 'と')}じる」。"
        ),
        "decoder_dt_bullet": (
            f"{_r('前', 'まえ')}の{_r('戦術', 'せんじゅつ')}が"
            f"{_r('残', 'のこ')}した{_r('次', 'つぎ')}の"
            f"{_r('部分', 'ぶぶん')}{_r('目標', 'もくひょう')}を"
            f"{_r('開始', 'かいし')}する{_r('箇条', 'かじょう')}"
            f"{_r('書', 'が')}き。"
        ),
        "decoder_dt_andintro": (
            f"「P かつ Q」の{_r('構成子', 'こうせいし')} ── "
            f"P の{_r('証明', 'しょうめい')}と Q の"
            f"{_r('証明', 'しょうめい')}を{_r('渡', 'わた')}す。ここでは "
            f"<code>«{_r('適応', 'てきおう')}» ∧ "
            f"«{_r('禁忌', 'きんき')}»</code> の"
            f"{_r('衝突', 'しょうとつ')}を{_r('組', 'く')}み"
            f"{_r('立', 'た')}てる。"
        ),
        "decoder_dt_false": (
            f"{_r('決', 'けっ')}して{_r('真', 'しん')}にならない"
            f"{_r('命題', 'めいだい')}。これを{_r('証明', 'しょうめい')}する"
            f"ということは、{_r('公理', 'こうり')}が{_r('互', 'たが')}いに"
            f"{_r('矛盾', 'むじゅん')}していることを"
            f"{_r('意味', 'いみ')}する。"
        ),
        "decoder_dt_absurd": (
            f"{_r('各', 'かく')}シナリオの{_r('最終', 'さいしゅう')}"
            f"{_r('定理', 'ていり')} ── {_r('主張', 'しゅちょう')}は "
            f"<code>False</code> なので、その"
            f"{_r('証明', 'しょうめい')}そのものが"
            f"{_r('矛盾', 'むじゅん')}である。"
        ),
        "decoder_dt_print_axioms": (
            f"メタコマンド：{_r('証明', 'しょうめい')}が{_r('実際', 'じっさい')}に"
            f"{_r('依拠', 'いきょ')}した{_r('公理', 'こうり')}をすべて"
            f"{_r('列挙', 'れっきょ')}し、ホストが <code>sorry</code> "
            f"{_r('仮', 'かり')}{_r('置', 'お')}きを"
            f"{_r('除外', 'じょがい')}できるようにする。"
        ),
        "alert_error_title": (
            f"{_r('検証', 'けんしょう')}を{_r('完了', 'かんりょう')}"
            f"できませんでした"
        ),
        "alert_collision_title": (
            f"ガイドライン{_r('衝突', 'しょうとつ')}を"
            f"{_r('形式的', 'けいしきてき')}に{_r('検証', 'けんしょう')}"
        ),
        "alert_collision_message_pre": (
            f"Lean 4 カーネルがこのシナリオに{_r('対', 'たい')}して "
        ),
        "alert_collision_message_mid": (
            f" の{_r('型', 'かた')}{_r('検査', 'けんさ')}を"
            f"{_r('完了', 'かんりょう')}しました。"
            f"{_r('符号化', 'ふごうか')}された{_r('臨床', 'りんしょう')}"
            f"ガイドラインは、{_r('患者', 'かんじゃ')}カルテに"
            f"{_r('適用', 'てきよう')}すると{_r('義務論的', 'ぎむろんてき')}"
            f"{_r('矛盾', 'むじゅん')}を{_r('証明', 'しょうめい')}します。"
            f"{_r('証明', 'しょうめい')}に{_r('関与', 'かんよ')}した"
            f"{_r('信頼', 'しんらい')}{_r('公理', 'こうり')}："
        ),
        "alert_unsound_title": (
            f"{_r('証明', 'しょうめい')}が{_r('不健全', 'ふけんぜん')}"
        ),
        "alert_unsound_message_pre": (
            f"Lean はファイルを{_r('受理', 'じゅり')}しましたが、"
            f"{_r('証明', 'しょうめい')}は "
        ),
        "alert_unsound_message_mid": (
            f" ── カーネルが{_r('矛盾', 'むじゅん')}を"
            f"{_r('実際', 'じっさい')}には{_r('確立', 'かくりつ')}していない"
            f"ことを{_r('意味', 'いみ')}する{_r('仮', 'かり')}"
            f"{_r('置', 'お')}き ── に{_r('依存', 'いぞん')}しています。"
        ),
        "alert_unsound_message_post": (
            f" のソースを{_r('監査', 'かんさ')}してください。"
        ),
        "alert_rejected_title": (
            f"Lean が{_r('証明', 'しょうめい')}を"
            f"{_r('却下', 'きゃっか')}しました"
        ),
        "alert_rejected_message_pre": f"Lean 4 コンパイラが ",
        "alert_rejected_message_post": (
            f" の{_r('型', 'かた')}{_r('検査', 'けんさ')}でエラーを"
            f"{_r('報告', 'ほうこく')}しました。{_r('符号化', 'ふごうか')}"
            f"された{_r('公理', 'こうり')}は{_r('期待', 'きたい')}される"
            f"{_r('矛盾', 'むじゅん')}を{_r('導出', 'どうしゅつ')}しません"
            f" ── {_r('以下', 'いか')}のコンパイラ"
            f"{_r('出力', 'しゅつりょく')}を"
            f"{_r('参照', 'さんしょう')}してください。"
        ),
        "alert_no_verdict_title": (
            f"{_r('判定', 'はんてい')}が{_r('生成', 'せいせい')}"
            f"されませんでした"
        ),
        "alert_no_verdict_message": (
            f"Lean コンパイラは{_r('実行', 'じっこう')}されましたが、"
            f"{_r('解析', 'かいせき')}{_r('可能', 'かのう')}な "
            f"<code>#print axioms</code> "
            f"{_r('依存', 'いぞん')}{_r('行', 'ぎょう')}を"
            f"{_r('出力', 'しゅつりょく')}しませんでした。"
            f"{_r('以下', 'いか')}のコンパイラ"
            f"{_r('出力', 'しゅつりょく')}を"
            f"{_r('確認', 'かくにん')}してください。"
        ),
        "translation_label": (
            f"{_r('平易', 'へいい')}な{_r('日本語訳', 'にほんごやく')}"
        ),
        "terminal_hint": f".lean ファイルのライブ{_r('評価', 'ひょうか')}",
        "terminal_no_output": (
            f"（{_r('出力', 'しゅつりょく')}は"
            f"{_r('取得', 'しゅとく')}されませんでした）"
        ),
    },
    "en": {
        "html_lang": "en",
        "page_title": "Verifiable Clinical Decision Support \u00b7 Epistemological Audit",
        "brand_h1": "Verifiable Clinical Decision Support",
        "brand_tagline": "Epistemological Audit \u00b7 Formal Polypharmacy Collision Detection",
        "header_meta_pill": "Guideline Collision Examples",
        "lang_switcher_label": "Language",
        "lang_ja_label": f"{_r('日本語', 'にほんご')}",
        "lang_en_label": "English",
        "sidebar_title": "Clinical Scenarios",
        "sidebar_note": (
            "Each scenario encodes two published clinical guidelines whose "
            "recommendations collide on a single patient context. The "
            "formal verification engine attempts to derive a logical "
            "contradiction from the encoded axioms."
        ),
        "copyright_affiliation": "Hokkaido University Hospital",
        "status_pending": "Awaiting Verification",
        "status_failed": "Verification Failed",
        "status_collision": "Collision Verified",
        "status_unsound": "Proof Unsound",
        "status_rejected": "Lean Rejected Proof",
        "status_no_verdict": "No Verdict",
        "patient_context_label": "Patient Context",
        "lean_mapping_label": "Lean Mapping",
        "legend_condition": "condition",
        "legend_finding": "finding",
        "legend_intervention": "intervention",
        "legend_indicated": "indicated",
        "legend_contraindicated": "contraindicated",
        "guidelines_heading": "Clinical Guidelines",
        "guideline_tag_a": "Guideline 1",
        "guideline_tag_b": "Guideline 2",
        "verify_button": "Run Lean Formal Verification",
        "verify_indicator": "Compiling axioms\u2026",
        "lean_heading": "Lean 4 Formalization",
        "code_frame_hint_pre": "every",
        "code_frame_hint_demo": "underlined",
        "code_frame_hint_post": "symbol has a hover explanation",
        "syntax_decoder_title": "Reading this Lean proof",
        "syntax_decoder_sub": (
            "No Lean or programming background needed. The groups below "
            "are a quick overview; every underlined "
        ),
        "syntax_decoder_sub_and": "and every underlined",
        "syntax_decoder_sub_demo_a": "symbol",
        "syntax_decoder_sub_demo_b": "phrase",
        "syntax_decoder_sub_post": (
            "in the code has a hover tooltip written specifically for its "
            "line \u2014 the name being declared, the claim being proved, the "
            "guideline axiom being applied to this patient."
        ),
        "decoder_group_structure": "File structure",
        "decoder_group_decls": "Declarations",
        "decoder_group_tactics": "Proof tactics",
        "decoder_group_contradiction": "Contradiction",
        "decoder_dt_import": "Load another Lean file \u2014 here, the shared medical vocabulary.",
        "decoder_dt_namespace": "Open a named section; every declaration inside gets that prefix.",
        "decoder_dt_open": "Refer to names in a namespace without repeating the prefix.",
        "decoder_dt_axiom": "A starting fact Lean accepts without proof \u2014 a guideline or a chart finding.",
        "decoder_dt_theorem": "A claim Lean accepts <em>only</em> after mechanically checking its proof.",
        "decoder_dt_xt_label": "X\u00a0:\u00a0T",
        "decoder_dt_xt": "Read <code>:</code> as \u201cis a\u201d. <code>JohnDoe\u00a0:\u00a0Patient</code> = \u201cJohnDoe is a Patient\u201d.",
        "decoder_dt_xy_label": "X\u00a0:=\u00a0Y",
        "decoder_dt_xy": "Read <code>:=</code> as \u201cis defined as\u201d. Names <code>X</code> after the content on the right.",
        "decoder_dt_by": "Switch into step-by-step tactic mode \u2014 a recipe for building the proof.",
        "decoder_dt_unfold": "\u201cReplace this name with its definition\u201d so its structure is visible.",
        "decoder_dt_apply": "\u201cUse this lemma; I\u2019ll prove its premises next\u201d as fresh sub-goals.",
        "decoder_dt_exact": "\u201cHere is a term that is exactly the proof required \u2014 close the step.\u201d",
        "decoder_dt_bullet": "Bullet that starts the next sub-goal left open by an earlier tactic.",
        "decoder_dt_andintro": "Constructor for \u201cP and Q\u201d \u2014 supply a proof of P and a proof of Q. Used here to assemble the <code>Indicated \u2227 Contraindicated</code> collision.",
        "decoder_dt_false": "The proposition that is never true. Proving it means the axioms contradict each other.",
        "decoder_dt_absurd": "The final theorem in each scenario \u2014 its claim is <code>False</code>, so its proof <em>is</em> the contradiction.",
        "decoder_dt_print_axioms": "Meta-command: lists every axiom the proof actually relied on, so the host can rule out <code>sorry</code> placeholders.",
        "alert_error_title": "Verification could not be completed",
        "alert_collision_title": "Guideline Collision Formally Verified",
        "alert_collision_message_pre": "The Lean 4 kernel typechecked ",
        "alert_collision_message_mid": " for this scenario. The encoded clinical guidelines, applied to the patient\u2019s chart, prove a deontic contradiction. Trusted axioms participating in the proof:",
        "alert_unsound_title": "Proof Unsound",
        "alert_unsound_message_pre": "Lean accepted the file but the proof depends on ",
        "alert_unsound_message_mid": " \u2014 a stub that means the contradiction was not actually established by the kernel. Audit the ",
        "alert_unsound_message_post": " source.",
        "alert_rejected_title": "Lean Rejected the Proof",
        "alert_rejected_message_pre": "The Lean 4 compiler reported errors typechecking ",
        "alert_rejected_message_post": ". The encoded axioms do not yield the expected contradiction \u2014 see the compiler output below.",
        "alert_no_verdict_title": "No Verdict Produced",
        "alert_no_verdict_message": "The Lean compiler ran but did not emit a parseable <code>#print axioms</code> dependency line. Review the compiler output below.",
        "translation_label": "Plain English Translation",
        "terminal_hint": "live evaluation of the .lean file",
        "terminal_no_output": "(no output captured)",
    },
}


def get_ui_strings(locale: str) -> dict[str, str]:
    """Return the full UI string table for ``locale``."""
    return UI_STRINGS[normalize_locale(locale)]


def other_locale(locale: str) -> str:
    """Return the locale toggled to its complement (only two are supported)."""
    return "en" if normalize_locale(locale) == "ja" else "ja"
