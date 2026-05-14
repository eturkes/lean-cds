"""Bilingual locale registry (ja|en) + UI string catalogs. JA is default; ``?lang=`` overrides cookie ``cds_lang``. UI chrome lives in ``UI_STRINGS`` here; scenario metadata in :mod:`scenarios`; Lean source in ``lean/<locale>/``."""

from __future__ import annotations

from typing import Final

DEFAULT_LOCALE: Final[str] = "ja"
SUPPORTED_LOCALES: Final[tuple[str, ...]] = ("ja", "en")
LANGUAGE_COOKIE: Final[str] = "cds_lang"


def normalize_locale(value: str | None) -> str:
    """Return a supported locale code, falling back to :data:`DEFAULT_LOCALE`."""
    if value is None:
        return DEFAULT_LOCALE
    candidate = value.strip().lower()
    if candidate in SUPPORTED_LOCALES:
        return candidate
    return DEFAULT_LOCALE


# UI string catalogs.

UI_STRINGS: Final[dict[str, dict[str, str]]] = {
    "ja": {
        "html_lang": "ja",
        "page_title": "検証可能な臨床意思決定支援 ・ 認識論的監査",
        "brand_h1": "検証可能な臨床意思決定支援",
        "brand_tagline": "認識論的監査 ・ ポリファーマシー衝突の形式検証",
        "header_meta_pill": "ガイドライン衝突の例",
        "lang_switcher_label": "言語",
        "lang_ja_label": "日本語",
        "lang_en_label": "English",
        "sidebar_title": "臨床シナリオ",
        "sidebar_note": (
            "各シナリオは、単一の患者状況において推奨が衝突する2つの公開"
            "臨床ガイドラインを符号化しています。形式検証エンジンは、"
            "符号化された公理から論理的矛盾を導出することを試みます。"
        ),
        "copyright_affiliation": "北海道大学病院",
        "status_pending": "検証待ち",
        "status_failed": "検証失敗",
        "status_collision": "衝突を検証済み",
        "status_unsound": "証明が不健全",
        "status_rejected": "Lean が証明を却下",
        "status_no_verdict": "判定なし",
        "patient_context_label": "患者背景",
        "lean_mapping_label": "Lean マッピング",
        "legend_condition": "病態",
        "legend_finding": "所見",
        "legend_intervention": "介入",
        "legend_indicated": "適応",
        "legend_contraindicated": "禁忌",
        "guidelines_heading": "臨床ガイドライン",
        "guideline_tag_a": "ガイドライン 1",
        "guideline_tag_b": "ガイドライン 2",
        "verify_button": "Lean 形式検証を実行",
        "verify_indicator": "公理をコンパイル中…",
        "lean_heading": "Lean 4 による形式化",
        "code_frame_hint_pre": "下線付きの",
        "code_frame_hint_demo": "記号",
        "code_frame_hint_post": "には説明のホバーがあります",
        "syntax_decoder_title": "この Lean 証明の読み方",
        "syntax_decoder_sub": (
            "Lean やプログラミングの予備知識は不要です。以下のグループは"
            "簡単な概要であり、コード中の下線付きの"
        ),
        "syntax_decoder_sub_and": "や下線付きの",
        "syntax_decoder_sub_demo_a": "記号",
        "syntax_decoder_sub_demo_b": "語句",
        "syntax_decoder_sub_post": (
            "には、その行のために書かれたホバーツールチップが用意されて"
            "います ── 宣言される名前、証明される主張、この患者に適用される"
            "ガイドラインの公理など。"
        ),
        "decoder_group_structure": "ファイル構造",
        "decoder_group_decls": "宣言",
        "decoder_group_tactics": "証明戦術",
        "decoder_group_contradiction": "矛盾",
        "decoder_dt_import": "別の Lean ファイルを読み込む。ここでは共有医療語彙。",
        "decoder_dt_namespace": "名前付きセクションを開く。内部の宣言にはその接頭辞が付く。",
        "decoder_dt_open": "接頭辞を繰り返さずに名前空間内の名前を参照する。",
        "decoder_dt_axiom": "Lean が証明なしに受け入れる前提 ── ガイドラインや患者所見。",
        "decoder_dt_theorem": "機械的に証明を検査した後にのみ Lean が受け入れる主張。",
        "decoder_dt_xt_label": "X : T",
        "decoder_dt_xt": "<code>:</code> は「は〜である」と読む。<code>«山田太郎» : «患者»</code> = 「«山田太郎» は «患者» である」。",
        "decoder_dt_xy_label": "X := Y",
        "decoder_dt_xy": "<code>:=</code> は「と定義する」と読む。右辺の内容に <code>X</code> という名前を与える。",
        "decoder_dt_by": "ステップごとの戦術モードに切り替える ── 証明を組み立てるレシピ。",
        "decoder_dt_unfold": "「この名前を定義で置き換える」── その構造を可視化する。",
        "decoder_dt_apply": "「この補題を使う。前提は次に証明する」と新しい部分目標として展開する。",
        "decoder_dt_exact": "「ここに示すのが必要な証明そのもの ── このステップを閉じる」。",
        "decoder_dt_bullet": "前の戦術が残した次の部分目標を開始する箇条書き。",
        "decoder_dt_andintro": "「P かつ Q」の構成子 ── P の証明と Q の証明を渡す。ここでは <code>«適応» ∧ «禁忌»</code> の衝突を組み立てる。",
        "decoder_dt_false": "決して真にならない命題。これを証明するということは、公理が互いに矛盾していることを意味する。",
        "decoder_dt_absurd": "各シナリオの最終定理 ── 主張は <code>False</code> なので、その証明そのものが矛盾である。",
        "decoder_dt_print_axioms": "メタコマンド：証明が実際に依拠した公理をすべて列挙し、ホストが <code>sorry</code> 仮置きを除外できるようにする。",
        "alert_error_title": "検証を完了できませんでした",
        "alert_collision_title": "ガイドライン衝突を形式的に検証",
        "alert_collision_message_pre": "Lean 4 カーネルがこのシナリオに対して ",
        "alert_collision_message_mid": " の型検査を完了しました。符号化された臨床ガイドラインは、患者カルテに適用すると義務論的矛盾を証明します。証明に関与した信頼公理：",
        "alert_unsound_title": "証明が不健全",
        "alert_unsound_message_pre": "Lean はファイルを受理しましたが、証明は ",
        "alert_unsound_message_mid": " ── カーネルが矛盾を実際には確立していないことを意味する仮置き ── に依存しています。",
        "alert_unsound_message_post": " のソースを監査してください。",
        "alert_rejected_title": "Lean が証明を却下しました",
        "alert_rejected_message_pre": "Lean 4 コンパイラが ",
        "alert_rejected_message_post": " の型検査でエラーを報告しました。符号化された公理は期待される矛盾を導出しません ── 以下のコンパイラ出力を参照してください。",
        "alert_no_verdict_title": "判定が生成されませんでした",
        "alert_no_verdict_message": "Lean コンパイラは実行されましたが、解析可能な <code>#print axioms</code> 依存行を出力しませんでした。以下のコンパイラ出力を確認してください。",
        "translation_label": "平易な日本語訳",
        "terminal_hint": ".lean ファイルのライブ評価",
        "terminal_no_output": "（出力は取得されませんでした）",
    },
    "en": {
        "html_lang": "en",
        "page_title": "Verifiable Clinical Decision Support · Epistemological Audit",
        "brand_h1": "Verifiable Clinical Decision Support",
        "brand_tagline": "Epistemological Audit · Formal Polypharmacy Collision Detection",
        "header_meta_pill": "Guideline Collision Examples",
        "lang_switcher_label": "Language",
        "lang_ja_label": "日本語",
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
        "verify_indicator": "Compiling axioms…",
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
            "line — the name being declared, the claim being proved, the "
            "guideline axiom being applied to this patient."
        ),
        "decoder_group_structure": "File structure",
        "decoder_group_decls": "Declarations",
        "decoder_group_tactics": "Proof tactics",
        "decoder_group_contradiction": "Contradiction",
        "decoder_dt_import": "Load another Lean file — here, the shared medical vocabulary.",
        "decoder_dt_namespace": "Open a named section; every declaration inside gets that prefix.",
        "decoder_dt_open": "Refer to names in a namespace without repeating the prefix.",
        "decoder_dt_axiom": "A starting fact Lean accepts without proof — a guideline or a chart finding.",
        "decoder_dt_theorem": "A claim Lean accepts <em>only</em> after mechanically checking its proof.",
        "decoder_dt_xt_label": "X&nbsp;:&nbsp;T",
        "decoder_dt_xt": "Read <code>:</code> as “is a”. <code>JohnDoe&nbsp;:&nbsp;Patient</code> = “JohnDoe is a Patient”.",
        "decoder_dt_xy_label": "X&nbsp;:=&nbsp;Y",
        "decoder_dt_xy": "Read <code>:=</code> as “is defined as”. Names <code>X</code> after the content on the right.",
        "decoder_dt_by": "Switch into step-by-step tactic mode — a recipe for building the proof.",
        "decoder_dt_unfold": "“Replace this name with its definition” so its structure is visible.",
        "decoder_dt_apply": "“Use this lemma; I'll prove its premises next” as fresh sub-goals.",
        "decoder_dt_exact": "“Here is a term that is exactly the proof required — close the step.”",
        "decoder_dt_bullet": "Bullet that starts the next sub-goal left open by an earlier tactic.",
        "decoder_dt_andintro": "Constructor for “P and Q” — supply a proof of P and a proof of Q. Used here to assemble the <code>Indicated ∧ Contraindicated</code> collision.",
        "decoder_dt_false": "The proposition that is never true. Proving it means the axioms contradict each other.",
        "decoder_dt_absurd": "The final theorem in each scenario — its claim is <code>False</code>, so its proof <em>is</em> the contradiction.",
        "decoder_dt_print_axioms": "Meta-command: lists every axiom the proof actually relied on, so the host can rule out <code>sorry</code> placeholders.",
        "alert_error_title": "Verification could not be completed",
        "alert_collision_title": "Guideline Collision Formally Verified",
        "alert_collision_message_pre": "The Lean 4 kernel typechecked ",
        "alert_collision_message_mid": " for this scenario. The encoded clinical guidelines, applied to the patient's chart, prove a deontic contradiction. Trusted axioms participating in the proof:",
        "alert_unsound_title": "Proof Unsound",
        "alert_unsound_message_pre": "Lean accepted the file but the proof depends on ",
        "alert_unsound_message_mid": " — a stub that means the contradiction was not actually established by the kernel. Audit the ",
        "alert_unsound_message_post": " source.",
        "alert_rejected_title": "Lean Rejected the Proof",
        "alert_rejected_message_pre": "The Lean 4 compiler reported errors typechecking ",
        "alert_rejected_message_post": ". The encoded axioms do not yield the expected contradiction — see the compiler output below.",
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
