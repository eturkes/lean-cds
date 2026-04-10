"""Bilingual clinical scenarios with authentic guideline excerpts.

Each scenario describes a single patient context in which two real-world
clinical guidelines collide. The Lean 4 source files are themselves
*localized*: ``lean/en/`` cites the American guidelines and uses
ASCII-romanized placeholder patient names (``JohnDoe`` etc.); ``lean/ja/``
cites the Japanese society guidelines and uses fully kanji-localized
identifiers (each French-quoted via Lean's ``«…»`` syntax — patient names
``«山田太郎»`` etc., predicates ``«適応»``/``«禁忌»``, and so on). Both
directories carry their own ``MedicalKnowledge.lean`` so each guideline
axiom is named after the society that actually published it.

This module declares:

* the per-locale ``Scenario`` registry with natural-language metadata
  for the UI panel,
* the locale-aware ``lean_subdir`` so the verifier can resolve the
  right ``ScenarioX.lean`` file at runtime.

The host process never injects user-controlled strings into the Lean
source. Each scenario references a pre-written file by name, and the
verifier invokes ``lean`` against that file directly.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from i18n import DEFAULT_LOCALE, SUPPORTED_LOCALES, normalize_locale


def _r(kanji: str, reading: str) -> str:
    """Return an HTML ``<ruby>`` annotation for *kanji* with *reading*."""
    return f"<ruby>{kanji}<rp>(</rp><rt>{reading}</rt><rp>)</rp></ruby>"


LEAN_DIR: Path = Path(__file__).resolve().parent / "lean"
KNOWLEDGE_BASE_MODULE: str = "MedicalKnowledge"


def knowledge_base_file(locale: str) -> Path:
    """Return the per-locale ``MedicalKnowledge.lean`` source path."""
    return LEAN_DIR / normalize_locale(locale) / f"{KNOWLEDGE_BASE_MODULE}.lean"


@dataclass(frozen=True)
class Guideline:
    source: str
    body: str


@dataclass(frozen=True)
class Scenario:
    id: str
    title: str
    subtitle: str
    patient_summary: str
    guideline_a: Guideline
    guideline_b: Guideline
    lean_filename: str
    lean_subdir: str
    audit_summary: str
    plain_english: str

    @property
    def lean_path(self) -> Path:
        return LEAN_DIR / self.lean_subdir / self.lean_filename

    @property
    def lean_dir(self) -> Path:
        return LEAN_DIR / self.lean_subdir

    def read_lean_source(self) -> str:
        return self.lean_path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# English (American clinical guidelines).
# ---------------------------------------------------------------------------

_EN_SCENARIO_A = Scenario(
    id="scenario-a",
    title="Hypertension vs. Severe Dehydration",
    subtitle="Thiazide diuretic — indicated and contraindicated",
    patient_summary=(
        "72-year-old patient with a 15-year history of "
        "<strong class=\"cds-cond\">essential hypertension</strong> "
        "presenting to the emergency department with acute gastroenteritis, "
        "<strong class=\"cds-find\">hypotension</strong> (BP 84/52), "
        "<strong class=\"cds-find\">tachycardia</strong>, "
        "<strong class=\"cds-find\">oliguria</strong>, "
        "<strong class=\"cds-find\">BUN/Cr ratio 28:1</strong>, and "
        "clinical signs of "
        "<strong class=\"cds-cond\">severe dehydration</strong>."
    ),
    guideline_a=Guideline(
        source="2017 ACC/AHA Guideline for the Prevention, Detection, "
               "Evaluation, and Management of High Blood Pressure in Adults — "
               "Section 8.1.6 (Choice of Initial Medication)",
        body=(
            "In adults with confirmed "
            "<strong class=\"cds-cond\">essential hypertension</strong> and "
            "an estimated 10-year atherosclerotic cardiovascular disease "
            "risk of \u226510%, initiation of pharmacologic therapy with a "
            "<strong class=\"cds-int\">thiazide-type diuretic</strong> "
            "(chlorthalidone 12.5\u201325 mg orally once daily preferred) "
            "is <strong class=\"cds-ind\">indicated</strong> as one of four "
            "co-equal first-line agent classes for long-term blood pressure "
            "control (Class I recommendation, Level of Evidence A). "
            "<strong class=\"cds-int\">Thiazide diuretics</strong> have "
            "demonstrated consistent mortality and major adverse "
            "cardiovascular event reduction across diverse adult populations "
            "and remain a cornerstone of guideline-directed antihypertensive "
            "therapy."
        ),
    ),
    guideline_b=Guideline(
        source="KDIGO Clinical Practice Guideline for Acute Kidney Injury — "
               "Section 3.4 (Use of Diuretics in AKI)",
        body=(
            "In any patient exhibiting clinical evidence of "
            "<strong class=\"cds-cond\">severe dehydration</strong> \u2014 "
            "including frank "
            "<strong class=\"cds-find\">hypotension</strong>, "
            "<strong class=\"cds-find\">sinus tachycardia</strong>, "
            "<strong class=\"cds-find\">oliguria</strong> (&lt;0.5 mL/kg/h), "
            "an elevated "
            "<strong class=\"cds-find\">BUN-to-creatinine ratio</strong> "
            "(&gt;20:1), and laboratory or physical findings of end-organ "
            "hypoperfusion \u2014 the initiation or continuation of any "
            "<strong class=\"cds-int\">diuretic therapy</strong> is "
            "<strong class=\"cds-con\">contraindicated</strong>. "
            "Administration of diuretics in this hemodynamic context "
            "carries an unacceptable risk of precipitating circulatory "
            "collapse, ischemic acute kidney injury, and accelerated "
            "multi-organ dysfunction (Grade 1B \u2014 strong recommendation, "
            "moderate-quality evidence)."
        ),
    ),
    lean_filename="ScenarioA.lean",
    lean_subdir="en",
    audit_summary=(
        "The Lean 4 Formalization above proves "
        "<code>Indicated JohnDoe ThiazideDiuretic \u2227 "
        "Contraindicated JohnDoe ThiazideDiuretic</code> from the AHA/ACC "
        "\u00a78.1.6 and KDIGO \u00a73.4 axioms, then derives "
        "<code>False</code> via "
        "<code>incompatible_modalities</code>. The kernel-trusted axiom "
        "list is the precise set of guidelines and chart findings "
        "participating in the contradiction."
    ),
    plain_english=(
        "The system has mathematically proven that, for this 72-year-old "
        "patient, it is impossible to simultaneously follow Guideline 1 "
        "(the ACC/AHA \u00a78.1.6 recommendation to start a thiazide "
        "diuretic for essential hypertension) and Guideline 2 (the KDIGO "
        "\u00a73.4 recommendation against diuretic use in the setting of "
        "severe dehydration) without violating the fundamental rule that "
        "a single drug cannot be both <em>indicated</em> and "
        "<em>contraindicated</em> for the same patient at the same time."
    ),
)


_EN_SCENARIO_B = Scenario(
    id="scenario-b",
    title="Diabetic Ketoacidosis vs. Severe Hypokalemia",
    subtitle="Intravenous insulin — indicated and contraindicated",
    patient_summary=(
        "34-year-old patient with type 1 diabetes mellitus presenting with "
        "polyuria, Kussmaul respirations, "
        "<strong class=\"cds-find\">plasma glucose 612 mg/dL</strong>, "
        "<strong class=\"cds-find\">arterial pH 7.18</strong>, "
        "<strong class=\"cds-find\">serum bicarbonate 9 mEq/L</strong>, "
        "anion gap 28, "
        "<strong class=\"cds-find\">moderate ketonuria</strong>, and a "
        "measured "
        "<strong class=\"cds-find\">serum potassium of 2.9 mEq/L</strong>."
    ),
    guideline_a=Guideline(
        source="ADA Standards of Care in Diabetes — Section 16: "
               "Diabetes Care in the Hospital (Hyperglycemic Crises)",
        body=(
            "For adult patients meeting diagnostic criteria for "
            "<strong class=\"cds-cond\">diabetic ketoacidosis</strong> "
            "(<strong class=\"cds-find\">plasma glucose &gt;250 mg/dL</strong>, "
            "<strong class=\"cds-find\">arterial pH &lt;7.30</strong>, "
            "<strong class=\"cds-find\">serum bicarbonate &lt;18 mEq/L</strong>, "
            "and the presence of ketonemia or "
            "<strong class=\"cds-find\">moderate ketonuria</strong>), "
            "prompt initiation of continuous "
            "<strong class=\"cds-int\">intravenous regular insulin</strong> "
            "infusion at 0.1 units/kg/hour is "
            "<strong class=\"cds-ind\">indicated</strong> to correct "
            "insulinopenia, suppress hepatic ketogenesis, and resolve the "
            "underlying metabolic acidosis (ADA evidence level A). "
            "Insulin therapy should not be delayed once "
            "<strong class=\"cds-cond\">DKA</strong> criteria are confirmed."
        ),
    ),
    guideline_b=Guideline(
        source="ADA Standards of Care in Diabetes — Section 16: "
               "DKA Management Algorithm (Potassium Safety Gate)",
        body=(
            "In any patient presenting with "
            "<strong class=\"cds-cond\">DKA</strong> who has a measured "
            "<strong class=\"cds-find\">serum potassium concentration below "
            "3.5 mEq/L</strong>, the administration of "
            "<strong class=\"cds-int\">insulin</strong> is "
            "<strong class=\"cds-con\">contraindicated</strong> "
            "until aggressive intravenous potassium replacement has restored "
            "serum potassium to \u22653.5 mEq/L. Insulin-induced "
            "transcellular potassium shift in the setting of preexisting "
            "<strong class=\"cds-cond\">hypokalemia</strong> carries an "
            "imminent risk of life-threatening ventricular arrhythmias, "
            "respiratory muscle paralysis, and cardiac arrest (ADA evidence "
            "level A \u2014 risk of harm)."
        ),
    ),
    lean_filename="ScenarioB.lean",
    lean_subdir="en",
    audit_summary=(
        "The Lean 4 Formalization above proves "
        "<code>Indicated JaneRoe IVRegularInsulin \u2227 "
        "Contraindicated JaneRoe IVRegularInsulin</code> from the ADA "
        "insulin-indication and ADA potassium-safety axioms, then derives "
        "<code>False</code> via "
        "<code>incompatible_modalities</code>. The literal reading of the "
        "ADA insulin axiom drops the K\u207a \u2265 3.5 mEq/L precondition, "
        "which is exactly the encoder bug the audit is designed to expose."
    ),
    plain_english=(
        "The system has mathematically proven that, for this 34-year-old "
        "patient in diabetic ketoacidosis with a serum potassium of "
        "2.9 mEq/L, it is impossible to simultaneously follow Guideline 1 "
        "(the ADA Standards of Care directive to start IV regular insulin "
        "in DKA) and Guideline 2 (the ADA DKA management algorithm\u2019s "
        "potassium safety gate that forbids insulin while serum potassium "
        "is below 3.5 mEq/L) without violating the fundamental rule that "
        "a single drug cannot be both <em>indicated</em> and "
        "<em>contraindicated</em> for the same patient at the same time."
    ),
)


_EN_SCENARIO_C = Scenario(
    id="scenario-c",
    title="Acute Panic Disorder vs. Severe Obstructive Sleep Apnea",
    subtitle="Benzodiazepine — indicated and contraindicated",
    patient_summary=(
        "58-year-old patient with a recent polysomnography-confirmed "
        "diagnosis of "
        "<strong class=\"cds-cond\">severe obstructive sleep apnea</strong> "
        "(<strong class=\"cds-find\">AHI 42 events/hour</strong>, nadir "
        "SpO\u2082 78%) "
        "<strong class=\"cds-find\">not yet established on PAP "
        "therapy</strong>, presenting to the emergency department with an "
        "<strong class=\"cds-cond\">acute, debilitating panic "
        "episode</strong> unresponsive to verbal de-escalation."
    ),
    guideline_a=Guideline(
        source="APA Practice Guideline for the Treatment of Patients With "
               "Panic Disorder — Acute Episode Management",
        body=(
            "For adults experiencing an "
            "<strong class=\"cds-cond\">acute, severe panic episode</strong> "
            "characterized by debilitating autonomic hyperarousal, "
            "depersonalization, and an impending sense of doom unresponsive "
            "to non-pharmacologic measures, "
            "<strong class=\"cds-int\">short-acting benzodiazepines</strong> "
            "(e.g., lorazepam 0.5\u20132 mg orally or intravenously) are "
            "<strong class=\"cds-ind\">indicated</strong> as recommended "
            "pharmacotherapy for rapid symptomatic relief and prevention of "
            "progression to a sustained anxiety crisis (APA recommendation "
            "category I, evidence level B)."
        ),
    ),
    guideline_b=Guideline(
        source="AASM Clinical Practice Guideline for the Treatment of Adult "
               "Obstructive Sleep Apnea — Sedative Avoidance Recommendation",
        body=(
            "In adults with a confirmed diagnosis of "
            "<strong class=\"cds-cond\">moderate-to-severe obstructive "
            "sleep apnea</strong> "
            "(<strong class=\"cds-find\">apnea\u2013hypopnea index "
            "\u226515 events/hour</strong>) who are "
            "<strong class=\"cds-find\">not yet established on effective "
            "positive airway pressure therapy</strong>, the use of "
            "<strong class=\"cds-int\">benzodiazepines</strong> and other "
            "central nervous system depressants is "
            "<strong class=\"cds-con\">contraindicated</strong>. "
            "These agents reduce upper airway dilator tone, blunt arousal "
            "responses to hypoxemia and hypercapnia, and are associated "
            "with prolonged apneic events, profound oxygen desaturations, "
            "and a markedly elevated risk of fatal nocturnal respiratory "
            "failure (AASM strong recommendation, moderate-quality "
            "evidence)."
        ),
    ),
    lean_filename="ScenarioC.lean",
    lean_subdir="en",
    audit_summary=(
        "The Lean 4 Formalization above proves "
        "<code>Indicated RichardRoe Benzodiazepine \u2227 "
        "Contraindicated RichardRoe Benzodiazepine</code> from the APA and "
        "AASM axioms, then derives <code>False</code> via "
        "<code>incompatible_modalities</code>. The audit surfaces the "
        "literal collision the APA recommendation produces in untreated "
        "severe OSA."
    ),
    plain_english=(
        "The system has mathematically proven that, for this 58-year-old "
        "patient with polysomnography-confirmed severe obstructive sleep "
        "apnea who is not yet on PAP therapy, it is impossible to "
        "simultaneously follow Guideline 1 (the APA panic-disorder "
        "recommendation to administer a short-acting benzodiazepine for "
        "an acute episode) and Guideline 2 (the AASM safety statement "
        "forbidding benzodiazepines in untreated severe OSA) without "
        "violating the fundamental rule that a single drug cannot be "
        "both <em>indicated</em> and <em>contraindicated</em> for the "
        "same patient at the same time."
    ),
)


# ---------------------------------------------------------------------------
# Japanese (Japanese clinical guidelines).
# ---------------------------------------------------------------------------

_JA_SCENARIO_A = Scenario(
    id="scenario-a",
    title=f"{_r('高血圧症', 'こうけつあつしょう')} {_r('対', 'たい')} {_r('重症', 'じゅうしょう')}{_r('脱水', 'だっすい')}",
    subtitle=f"サイアザイド{_r('系', 'けい')}{_r('利尿薬', 'りにょうやく')} ── {_r('適応', 'てきおう')}かつ{_r('禁忌', 'きんき')}",
    patient_summary=(
        f"15{_r('年', 'ねん')}{_r('来', 'らい')}の<strong class=\"cds-cond\">{_r('本態性', 'ほんたいせい')}{_r('高血圧', 'こうけつあつ')}</strong>"
        f"の{_r('既往', 'きおう')}を{_r('有', 'ゆう')}する72{_r('歳', 'さい')}の{_r('患者', 'かんじゃ')}。{_r('急性', 'きゅうせい')}{_r('胃腸炎', 'いちょうえん')}に{_r('伴', 'ともな')}い{_r('救急', 'きゅうきゅう')}{_r('外来', 'がいらい')}を{_r('受診', 'じゅしん')}し、"
        f"<strong class=\"cds-find\">{_r('低血圧', 'ていけつあつ')}</strong>（{_r('血圧', 'けつあつ')} 84/52 mmHg）、"
        f"<strong class=\"cds-find\">{_r('頻脈', 'ひんみゃく')}</strong>、"
        f"<strong class=\"cds-find\">{_r('乏尿', 'ぼうにょう')}</strong>、"
        f"<strong class=\"cds-find\">BUN/Cr {_r('比', 'ひ')} 28:1</strong>、"
        f"ならびに<strong class=\"cds-cond\">{_r('重症', 'じゅうしょう')}{_r('脱水', 'だっすい')}</strong>"
        f"の{_r('臨床', 'りんしょう')}{_r('所見', 'しょけん')}を{_r('呈', 'てい')}している。"
    ),
    guideline_a=Guideline(
        source=(
            f"{_r('日本', 'にほん')}{_r('高血圧', 'こうけつあつ')}{_r('学会', 'がっかい')}『{_r('高血圧', 'こうけつあつ')}{_r('治療', 'ちりょう')}ガイドライン2019（JSH2019）』── "
            f"{_r('第', 'だい')}5{_r('章', 'しょう')}「{_r('降圧薬', 'こうあつやく')}」{_r('積極的', 'せっきょくてき')}{_r('適応', 'てきおう')}のない{_r('高血圧', 'こうけつあつ')}の{_r('第一選択薬', 'だいいちせんたくやく')}"
        ),
        body=(
            f"{_r('確定', 'かくてい')}{_r('診断', 'しんだん')}された<strong class=\"cds-cond\">{_r('本態性', 'ほんたいせい')}{_r('高血圧', 'こうけつあつ')}</strong>"
            f"を{_r('有', 'ゆう')}する{_r('成人', 'せいじん')}で、{_r('積極的', 'せっきょくてき')}{_r('適応', 'てきおう')}がない{_r('場合', 'ばあい')}、"
            f"<strong class=\"cds-int\">サイアザイド{_r('系', 'けい')}{_r('利尿薬', 'りにょうやく')}</strong>"
            f"（{_r('少量', 'しょうりょう')}{_r('投与', 'とうよ')}を{_r('原則', 'げんそく')}とする）は、Ca{_r('拮抗薬', 'きっこうやく')}および ARB／ACE {_r('阻害薬', 'そがいやく')}と"
            f"{_r('並', 'なら')}ぶ{_r('第一選択', 'だいいちせんたく')}{_r('降圧薬', 'こうあつやく')}として"
            f"<strong class=\"cds-ind\">{_r('適応', 'てきおう')}</strong>される"
            f"（{_r('推奨', 'すいしょう')}グレード A、エビデンスレベル I）。{_r('本', 'ほん')}ガイドラインは、"
            f"{_r('食塩', 'しょくえん')}{_r('摂取量', 'せっしゅりょう')}の{_r('多', 'おお')}い{_r('日本人', 'にほんじん')}{_r('集団', 'しゅうだん')}および{_r('高齢者', 'こうれいしゃ')}において"
            f"<strong class=\"cds-int\">サイアザイド{_r('系', 'けい')}{_r('利尿薬', 'りにょうやく')}</strong>"
            f"の{_r('有用性', 'ゆうようせい')}が{_r('高', 'たか')}いことを{_r('明記', 'めいき')}しており、{_r('長期', 'ちょうき')}{_r('血圧', 'けつあつ')}{_r('管理', 'かんり')}において"
            f"ガイドラインに{_r('基', 'もと')}づく{_r('薬物療法', 'やくぶつりょうほう')}の{_r('中核', 'ちゅうかく')}を{_r('担', 'にな')}う。"
        ),
    ),
    guideline_b=Guideline(
        source=(
            f"{_r('日本', 'にほん')}{_r('腎臓', 'じんぞう')}{_r('学会', 'がっかい')}ほか{_r('合同', 'ごうどう')}『AKI（{_r('急性', 'きゅうせい')}{_r('腎障害', 'じんしょうがい')}）{_r('診療', 'しんりょう')}ガイドライン2016』── "
            f"{_r('第', 'だい')}3{_r('章', 'しょう')} CQ「{_r('利尿薬', 'りにょうやく')}の AKI {_r('予防', 'よぼう')}・{_r('治療', 'ちりょう')}における{_r('推奨', 'すいしょう')}」"
        ),
        body=(
            f"<strong class=\"cds-cond\">{_r('重症', 'じゅうしょう')}{_r('脱水', 'だっすい')}</strong>"
            f"の{_r('臨床的', 'りんしょうてき')}{_r('所見', 'しょけん')} ── すなわち{_r('明', 'あき')}らかな"
            f"<strong class=\"cds-find\">{_r('低血圧', 'ていけつあつ')}</strong>、"
            f"<strong class=\"cds-find\">{_r('洞性', 'どうせい')}{_r('頻脈', 'ひんみゃく')}</strong>、"
            f"<strong class=\"cds-find\">{_r('乏尿', 'ぼうにょう')}</strong>"
            f"（&lt;0.5 mL/kg/{_r('時', 'じ')}）、"
            f"<strong class=\"cds-find\">BUN/Cr {_r('比', 'ひ')}の{_r('上昇', 'じょうしょう')}</strong>"
            f"（&gt;20:1）、ならびに{_r('末梢', 'まっしょう')}{_r('臓器', 'ぞうき')}{_r('灌流', 'かんりゅう')}{_r('低下', 'ていか')}を{_r('示', 'しめ')}す{_r('検査', 'けんさ')}・{_r('身体', 'しんたい')}{_r('所見', 'しょけん')} ── "
            f"を{_r('呈', 'てい')}する{_r('患者', 'かんじゃ')}においては、いかなる"
            f"<strong class=\"cds-int\">{_r('利尿薬', 'りにょうやく')}{_r('療法', 'りょうほう')}</strong>"
            f"の{_r('開始', 'かいし')}または{_r('継続', 'けいぞく')}も"
            f"<strong class=\"cds-con\">{_r('絶対', 'ぜったい')}{_r('禁忌', 'きんき')}</strong>"
            f"である。{_r('本', 'ほん')}ガイドラインは、まず{_r('十分', 'じゅうぶん')}な{_r('輸液', 'ゆえき')}による{_r('容量', 'ようりょう')}{_r('補正', 'ほせい')}を"
            f"{_r('行', 'おこな')}うことを{_r('推奨', 'すいしょう')}し、AKI の{_r('予防', 'よぼう')}および{_r('治療', 'ちりょう')}{_r('目的', 'もくてき')}での{_r('利尿薬', 'りにょうやく')}{_r('投与', 'とうよ')}は"
            f"{_r('推奨', 'すいしょう')}しない。{_r('本', 'ほん')}{_r('血行動態', 'けっこうどうたい')}{_r('下', 'か')}での{_r('利尿薬', 'りにょうやく')}{_r('投与', 'とうよ')}は、{_r('循環', 'じゅんかん')}{_r('虚脱', 'きょだつ')}、"
            f"{_r('虚血性', 'きょけつせい')}{_r('急性', 'きゅうせい')}{_r('腎障害', 'じんしょうがい')}、ならびに{_r('多臓器', 'たぞうき')}{_r('不全', 'ふぜん')}{_r('進行', 'しんこう')}の{_r('容認', 'ようにん')}できない"
            f"リスクを{_r('伴', 'ともな')}う（{_r('推奨度', 'すいしょうど')} 1、エビデンスレベル B）。"
        ),
    ),
    lean_filename="ScenarioA.lean",
    lean_subdir="ja",
    audit_summary=(
        f"{_r('上記', 'じょうき')}の Lean 4 {_r('形式化', 'けいしきか')}は、<code>«{_r('高血圧', 'こうけつあつ')}2019_{_r('第', 'だい')}5{_r('章', 'しょう')}_{_r('第一選択', 'だいいちせんたく')}»</code> と "
        f"<code>«{_r('腎臓', 'じんぞう')}AKI2016_{_r('利尿薬', 'りにょうやく')}»</code> の{_r('公理', 'こうり')}から "
        f"<code>«{_r('適応', 'てきおう')}» «{_r('山田', 'やまだ')}{_r('太郎', 'たろう')}» «{_r('治療', 'ちりょう')}».«サイアザイド{_r('系', 'けい')}{_r('利尿薬', 'りにょうやく')}» \u2227 "
        f"«{_r('禁忌', 'きんき')}» «{_r('山田', 'やまだ')}{_r('太郎', 'たろう')}» «{_r('治療', 'ちりょう')}».«サイアザイド{_r('系', 'けい')}{_r('利尿薬', 'りにょうやく')}»</code> を"
        f"{_r('証明', 'しょうめい')}し、<code>«{_r('治療法', 'ちりょうほう')}の{_r('両立', 'りょうりつ')}{_r('不能性', 'ふのうせい')}»</code> を{_r('介', 'かい')}して "
        f"<code>False</code> を{_r('導出', 'どうしゅつ')}します。カーネルが{_r('信頼', 'しんらい')}する{_r('公理', 'こうり')}リストは、"
        f"{_r('矛盾', 'むじゅん')}に{_r('関与', 'かんよ')}したガイドラインと{_r('患者', 'かんじゃ')}{_r('所見', 'しょけん')}の{_r('正確', 'せいかく')}な{_r('集合', 'しゅうごう')}です。"
    ),
    plain_english=(
        f"{_r('本', 'ほん')}システムは、この72{_r('歳', 'さい')}の{_r('患者', 'かんじゃ')}について、ガイドライン 1（{_r('本態性', 'ほんたいせい')}"
        f"{_r('高血圧', 'こうけつあつ')}に{_r('対', 'たい')}しサイアザイド{_r('系', 'けい')}{_r('利尿薬', 'りにょうやく')}を{_r('第一選択薬', 'だいいちせんたくやく')}として{_r('推奨', 'すいしょう')}する"
        f"JSH2019 {_r('第', 'だい')}5{_r('章', 'しょう')}）とガイドライン 2（{_r('重症', 'じゅうしょう')}{_r('脱水', 'だっすい')}においていかなる{_r('利尿薬', 'りにょうやく')}"
        f"{_r('投与', 'とうよ')}も{_r('推奨', 'すいしょう')}しない JSN AKI {_r('診療', 'しんりょう')}ガイドライン2016）を{_r('同時', 'どうじ')}に{_r('遵守', 'じゅんしゅ')}する"
        f"ことが、「{_r('同一', 'どういつ')}の{_r('薬剤', 'やくざい')}を{_r('同一', 'どういつ')}{_r('患者', 'かんじゃ')}に{_r('対', 'たい')}し{_r('同時', 'どうじ')}に<em>{_r('適応', 'てきおう')}</em>かつ"
        f"<em>{_r('禁忌', 'きんき')}</em>とすることはできない」という{_r('基本', 'きほん')}{_r('原則', 'げんそく')}に{_r('違反', 'いはん')}せずには"
        f"{_r('不可能', 'ふかのう')}であることを{_r('数学的', 'すうがくてき')}に{_r('証明', 'しょうめい')}しました。"
    ),
)


_JA_SCENARIO_B = Scenario(
    id="scenario-b",
    title=f"{_r('糖尿病性', 'とうにょうびょうせい')}ケトアシドーシス {_r('対', 'たい')} {_r('重症', 'じゅうしょう')}{_r('低', 'てい')}カリウム{_r('血症', 'けっしょう')}",
    subtitle=f"{_r('経静脈', 'けいじょうみゃく')}インスリン ── {_r('適応', 'てきおう')}かつ{_r('禁忌', 'きんき')}",
    patient_summary=(
        f"1{_r('型', 'がた')}{_r('糖尿病', 'とうにょうびょう')}を{_r('有', 'ゆう')}する34{_r('歳', 'さい')}の{_r('患者', 'かんじゃ')}。{_r('多尿', 'たにょう')}、Kussmaul {_r('呼吸', 'こきゅう')}、"
        f"<strong class=\"cds-find\">{_r('血漿', 'けっしょう')}グルコース 612 mg/dL</strong>、"
        f"<strong class=\"cds-find\">{_r('動脈血', 'どうみゃくけつ')} pH 7.18</strong>、"
        f"<strong class=\"cds-find\">{_r('血清', 'けっせい')}{_r('重炭酸', 'じゅうたんさん')} 9 mEq/L</strong>、"
        f"アニオンギャップ 28、"
        f"<strong class=\"cds-find\">{_r('中等度', 'ちゅうとうど')}ケトン{_r('尿', 'にょう')}</strong>、"
        f"ならびに{_r('測定値', 'そくていち')}"
        f"<strong class=\"cds-find\">{_r('血清', 'けっせい')}カリウム 2.9 mEq/L</strong>"
        f"を{_r('呈', 'てい')}している。"
    ),
    guideline_a=Guideline(
        source=(
            f"{_r('日本', 'にほん')}{_r('糖尿病', 'とうにょうびょう')}{_r('学会', 'がっかい')}『{_r('糖尿病', 'とうにょうびょう')}{_r('診療', 'しんりょう')}ガイドライン2024』── "
            f"{_r('第', 'だい')}20-1{_r('項', 'こう')}「{_r('糖尿病性', 'とうにょうびょうせい')}ケトアシドーシスの{_r('診断', 'しんだん')}と{_r('治療', 'ちりょう')}」"
        ),
        body=(
            f"<strong class=\"cds-cond\">{_r('糖尿病性', 'とうにょうびょうせい')}ケトアシドーシス</strong>"
            f"（<strong class=\"cds-find\">{_r('血漿', 'けっしょう')}グルコース &gt;250 mg/dL</strong>、"
            f"<strong class=\"cds-find\">{_r('動脈血', 'どうみゃくけつ')} pH &lt;7.30</strong>、"
            f"<strong class=\"cds-find\">{_r('血清', 'けっせい')}{_r('重炭酸', 'じゅうたんさん')} &lt;18 mEq/L</strong>、"
            f"ならびにケトン{_r('血症', 'けっしょう')}または"
            f"<strong class=\"cds-find\">{_r('中等度', 'ちゅうとうど')}{_r('以上', 'いじょう')}のケトン{_r('尿', 'にょう')}</strong>"
            f"の{_r('存在', 'そんざい')}）の{_r('診断基準', 'しんだんきじゅん')}を{_r('満', 'み')}たす{_r('成人', 'せいじん')}{_r('患者', 'かんじゃ')}に{_r('対', 'たい')}しては、"
            f"<strong class=\"cds-int\">{_r('速効型', 'そっこうがた')}インスリンの{_r('持続', 'じぞく')}{_r('静注', 'じょうちゅう')}</strong>"
            f"（0.1 {_r('単位', 'たんい')}/kg/{_r('時', 'じ')}）の{_r('速', 'すみ')}やかな{_r('開始', 'かいし')}が、インスリン{_r('欠乏', 'けつぼう')}の{_r('補正', 'ほせい')}、"
            f"{_r('肝', 'かん')}でのケトン{_r('体', 'たい')}{_r('産生', 'さんせい')}{_r('抑制', 'よくせい')}、ならびに{_r('代謝性', 'たいしゃせい')}アシドーシスの{_r('改善', 'かいぜん')}を"
            f"{_r('目的', 'もくてき')}として"
            f"<strong class=\"cds-ind\">{_r('適応', 'てきおう')}</strong>される"
            f"（{_r('推奨', 'すいしょう')}グレード A、エビデンスレベル 1）。"
            f"<strong class=\"cds-cond\">DKA</strong> {_r('診断基準', 'しんだんきじゅん')}が{_r('確認', 'かくにん')}され{_r('次第', 'しだい')}、"
            f"インスリン{_r('療法', 'りょうほう')}を{_r('遅延', 'ちえん')}させてはならない。"
        ),
    ),
    guideline_b=Guideline(
        source=(
            f"{_r('日本', 'にほん')}{_r('糖尿病', 'とうにょうびょう')}{_r('学会', 'がっかい')}『{_r('糖尿病', 'とうにょうびょう')}{_r('診療', 'しんりょう')}ガイドライン2024』── "
            f"{_r('第', 'だい')}20-1{_r('項', 'こう')} DKA {_r('治療', 'ちりょう')}アルゴリズム「{_r('血清', 'けっせい')}カリウム{_r('管理', 'かんり')}」"
        ),
        body=(
            f"<strong class=\"cds-cond\">DKA</strong> を{_r('呈', 'てい')}する{_r('患者', 'かんじゃ')}で、"
            f"<strong class=\"cds-find\">{_r('血清', 'けっせい')}カリウム{_r('濃度', 'のうど')}が 3.3 mEq/L {_r('未満', 'みまん')}</strong>"
            f"と{_r('測定', 'そくてい')}された{_r('症例', 'しょうれい')}においては、{_r('十分', 'じゅうぶん')}な{_r('経静脈', 'けいじょうみゃく')}カリウム{_r('補充', 'ほじゅう')}により"
            f"{_r('血清', 'けっせい')}カリウムが 3.3 mEq/L {_r('以上', 'いじょう')}に{_r('回復', 'かいふく')}するまで、"
            f"<strong class=\"cds-int\">インスリン</strong>"
            f"の{_r('投与', 'とうよ')}は"
            f"<strong class=\"cds-con\">{_r('厳禁', 'げんきん')}</strong>"
            f"とする。{_r('先行', 'せんこう')}する"
            f"<strong class=\"cds-cond\">{_r('低', 'てい')}カリウム{_r('血症', 'けっしょう')}</strong>"
            f"の{_r('状態', 'じょうたい')}{_r('下', 'か')}でインスリンが{_r('惹起', 'じゃっき')}する{_r('細胞', 'さいぼう')}{_r('内', 'ない')}カリウム{_r('移動', 'いどう')}は、"
            f"{_r('致死的', 'ちしてき')}な{_r('心室性', 'しんしつせい')}{_r('不整脈', 'ふせいみゃく')}、{_r('呼吸筋', 'こきゅうきん')}{_r('麻痺', 'まひ')}、ならびに{_r('心停止', 'しんていし')}の{_r('差', 'さ')}し{_r('迫', 'せま')}った"
            f"リスクを{_r('伴', 'ともな')}う（{_r('推奨', 'すいしょう')}グレード A、エビデンスレベル 1 ── {_r('害', 'がい')}）。"
        ),
    ),
    lean_filename="ScenarioB.lean",
    lean_subdir="ja",
    audit_summary=(
        f"{_r('上記', 'じょうき')}の Lean 4 {_r('形式化', 'けいしきか')}は、{_r('日本', 'にほん')}{_r('糖尿病', 'とうにょうびょう')}{_r('学会', 'がっかい')}『{_r('糖尿病', 'とうにょうびょう')}{_r('診療', 'しんりょう')}ガイドライン"
        f"2024』{_r('第', 'だい')}20-1{_r('項', 'こう')}の DKA {_r('適応', 'てきおう')}{_r('公理', 'こうり')} "
        f"<code>«{_r('糖尿病', 'とうにょうびょう')}2024_{_r('第', 'だい')}20_1{_r('項', 'こう')}_DKA»</code> と{_r('血清', 'けっせい')}カリウム{_r('管理', 'かんり')}{_r('公理', 'こうり')} "
        f"<code>«{_r('糖尿病', 'とうにょうびょう')}2024_{_r('第', 'だい')}20_1{_r('項', 'こう')}_K{_r('管理', 'かんり')}»</code> から "
        f"<code>«{_r('適応', 'てきおう')}» «{_r('鈴木', 'すずき')}{_r('花子', 'はなこ')}» «{_r('治療', 'ちりょう')}».«{_r('速効型', 'そっこうがた')}インスリン{_r('静注', 'じょうちゅう')}» \u2227 "
        f"«{_r('禁忌', 'きんき')}» «{_r('鈴木', 'すずき')}{_r('花子', 'はなこ')}» «{_r('治療', 'ちりょう')}».«{_r('速効型', 'そっこうがた')}インスリン{_r('静注', 'じょうちゅう')}»</code> を"
        f"{_r('証明', 'しょうめい')}し、<code>«{_r('治療法', 'ちりょうほう')}の{_r('両立', 'りょうりつ')}{_r('不能性', 'ふのうせい')}»</code> を{_r('介', 'かい')}して "
        f"<code>False</code> を{_r('導出', 'どうしゅつ')}します。インスリン{_r('適応', 'てきおう')}{_r('公理', 'こうり')}を{_r('文字通', 'もじどお')}り"
        f"{_r('読', 'よ')}むと K\u207a \u2265 3.3 mEq/L の{_r('前提条件', 'ぜんていじょうけん')}が{_r('抜', 'ぬ')}け{_r('落', 'お')}ちており、"
        f"それこそが{_r('本', 'ほん')}{_r('監査', 'かんさ')}が{_r('暴', 'あば')}き{_r('出', 'だ')}すよう{_r('設計', 'せっけい')}された{_r('符号化', 'ふごうか')}バグです。"
    ),
    plain_english=(
        f"{_r('本', 'ほん')}システムは、{_r('血清', 'けっせい')}カリウム 2.9 mEq/L の{_r('糖尿病性', 'とうにょうびょうせい')}ケトアシドーシス"
        f"を{_r('呈', 'てい')}するこの34{_r('歳', 'さい')}の{_r('患者', 'かんじゃ')}について、ガイドライン 1（DKA に{_r('対', 'たい')}し{_r('速効型', 'そっこうがた')}"
        f"インスリン{_r('持続', 'じぞく')}{_r('静注', 'じょうちゅう')}の{_r('開始', 'かいし')}を{_r('指示', 'しじ')}する『{_r('糖尿病', 'とうにょうびょう')}{_r('診療', 'しんりょう')}ガイドライン2024』"
        f"{_r('第', 'だい')}20-1{_r('項', 'こう')}）とガイドライン 2（{_r('血清', 'けっせい')}カリウムが 3.3 mEq/L {_r('未満', 'みまん')}の{_r('間', 'あいだ')}は"
        f"インスリン{_r('投与', 'とうよ')}を{_r('厳禁', 'げんきん')}とする{_r('同', 'どう')}ガイドラインの{_r('血清', 'けっせい')}カリウム{_r('管理', 'かんり')}{_r('項', 'こう')}）を"
        f"{_r('同時', 'どうじ')}に{_r('遵守', 'じゅんしゅ')}することが、「{_r('同一', 'どういつ')}の{_r('薬剤', 'やくざい')}を{_r('同一', 'どういつ')}{_r('患者', 'かんじゃ')}に{_r('対', 'たい')}し{_r('同時', 'どうじ')}に"
        f"<em>{_r('適応', 'てきおう')}</em>かつ<em>{_r('禁忌', 'きんき')}</em>とすることはできない」という{_r('基本', 'きほん')}{_r('原則', 'げんそく')}"
        f"に{_r('違反', 'いはん')}せずには{_r('不可能', 'ふかのう')}であることを{_r('数学的', 'すうがくてき')}に{_r('証明', 'しょうめい')}しました。"
    ),
)


_JA_SCENARIO_C = Scenario(
    id="scenario-c",
    title=f"{_r('急性', 'きゅうせい')}パニック{_r('症', 'しょう')} {_r('対', 'たい')} {_r('重症', 'じゅうしょう')}{_r('閉塞性', 'へいそくせい')}{_r('睡眠時', 'すいみんじ')}{_r('無呼吸', 'むこきゅう')}",
    subtitle=f"ベンゾジアゼピン ── {_r('適応', 'てきおう')}かつ{_r('禁忌', 'きんき')}",
    patient_summary=(
        f"{_r('終夜', 'しゅうや')}{_r('睡眠', 'すいみん')}ポリグラフ{_r('検査', 'けんさ')}で{_r('確定', 'かくてい')}{_r('診断', 'しんだん')}された"
        f"<strong class=\"cds-cond\">{_r('重症', 'じゅうしょう')}{_r('閉塞性', 'へいそくせい')}{_r('睡眠時', 'すいみんじ')}{_r('無呼吸', 'むこきゅう')}</strong>"
        f"（<strong class=\"cds-find\">{_r('無呼吸', 'むこきゅう')}{_r('低', 'てい')}{_r('呼吸', 'こきゅう')}{_r('指数', 'しすう')} 42 {_r('回', 'かい')}/{_r('時', 'じ')}</strong>、"
        f"{_r('最低', 'さいてい')} SpO\u2082 78%）"
        f"を{_r('有', 'ゆう')}し<strong class=\"cds-find\">{_r('未', 'いま')}だ{_r('持続', 'じぞく')}{_r('陽圧', 'ようあつ')}{_r('呼吸', 'こきゅう')}（CPAP）{_r('療法', 'りょうほう')}"
        f"が{_r('導入', 'どうにゅう')}されていない</strong>58{_r('歳', 'さい')}の{_r('患者', 'かんじゃ')}。{_r('言語的', 'げんごてき')}{_r('鎮静', 'ちんせい')}に{_r('反応', 'はんのう')}しない"
        f"<strong class=\"cds-cond\">{_r('急性', 'きゅうせい')}かつ{_r('重度', 'じゅうど')}のパニック{_r('発作', 'ほっさ')}</strong>"
        f"を{_r('呈', 'てい')}し{_r('救急', 'きゅうきゅう')}{_r('外来', 'がいらい')}を{_r('受診', 'じゅしん')}。"
    ),
    guideline_a=Guideline(
        source=(
            f"{_r('日本', 'にほん')}{_r('不安', 'ふあん')}{_r('症', 'しょう')}{_r('学会', 'がっかい')}・{_r('日本', 'にほん')}{_r('神経', 'しんけい')}{_r('精神', 'せいしん')}{_r('薬理', 'やくり')}{_r('学会', 'がっかい')} {_r('合同', 'ごうどう')}『パニック{_r('症', 'しょう')}の"
            f"{_r('診療', 'しんりょう')}ガイドライン（2025{_r('年版', 'ねんばん')}）』── {_r('急性期', 'きゅうせいき')}{_r('薬物療法', 'やくぶつりょうほう')}"
        ),
        body=(
            f"{_r('成人', 'せいじん')}における"
            f"<strong class=\"cds-cond\">{_r('急性', 'きゅうせい')}かつ{_r('重度', 'じゅうど')}のパニック{_r('発作', 'ほっさ')}</strong>"
            f"── {_r('自律', 'じりつ')}{_r('神経', 'しんけい')}{_r('過活動', 'かかつどう')}、{_r('離人感', 'りじんかん')}、ならびに{_r('切迫', 'せっぱく')}した{_r('破局感', 'はきょくかん')}を{_r('特徴', 'とくちょう')}と"
            f"し、{_r('非薬物', 'ひやくぶつ')}{_r('療法', 'りょうほう')}に{_r('反応', 'はんのう')}しないもの ── に{_r('対', 'たい')}しては、"
            f"<strong class=\"cds-int\">{_r('高力価', 'こうりきか')}ベンゾジアゼピン</strong>"
            f"（{_r('例', 'れい')}：ロラゼパム 0.5\u20132 mg {_r('経口', 'けいこう')}または{_r('静注', 'じょうちゅう')}、"
            f"アルプラゾラム、クロナゼパム）が、{_r('迅速', 'じんそく')}な{_r('症状', 'しょうじょう')}{_r('緩和', 'かんわ')}ならびに"
            f"{_r('持続的', 'じぞくてき')}な{_r('不安', 'ふあん')}{_r('発作', 'ほっさ')}への{_r('進展', 'しんてん')}{_r('予防', 'よぼう')}のための{_r('第一選択', 'だいいちせんたく')}{_r('薬物療法', 'やくぶつりょうほう')}として"
            f"<strong class=\"cds-ind\">{_r('適応', 'てきおう')}</strong>される"
            f"（{_r('推奨度', 'すいしょうど')} 1、エビデンスレベル B）。SSRI の{_r('効果', 'こうか')}{_r('発現', 'はつげん')}までの"
            f"{_r('短期', 'たんき')}{_r('併用', 'へいよう')}が{_r('標準的', 'ひょうじゅんてき')}{_r('位置付', 'いちづ')}けである。"
        ),
    ),
    guideline_b=Guideline(
        source=(
            f"{_r('日本', 'にほん')}{_r('呼吸器', 'こきゅうき')}{_r('学会', 'がっかい')}『{_r('睡眠時', 'すいみんじ')}{_r('無呼吸', 'むこきゅう')}{_r('症候群', 'しょうこうぐん')}（SAS）の{_r('診療', 'しんりょう')}"
            f"ガイドライン2020』── ベンゾジアゼピン{_r('使用', 'しよう')}に{_r('関', 'かん')}する"
            f"{_r('薬物療法', 'やくぶつりょうほう')}{_r('安全', 'あんぜん')}{_r('声明', 'せいめい')}"
        ),
        body=(
            f"<strong class=\"cds-cond\">{_r('中等症', 'ちゅうとうしょう')}から{_r('重症', 'じゅうしょう')}の{_r('閉塞性', 'へいそくせい')}{_r('睡眠時', 'すいみんじ')}{_r('無呼吸', 'むこきゅう')}</strong>"
            f"（<strong class=\"cds-find\">{_r('無呼吸', 'むこきゅう')}{_r('低', 'てい')}{_r('呼吸', 'こきゅう')}{_r('指数', 'しすう')} \u226515 {_r('回', 'かい')}/{_r('時', 'じ')}</strong>）"
            f"の{_r('確定', 'かくてい')}{_r('診断', 'しんだん')}を{_r('有', 'ゆう')}し、"
            f"<strong class=\"cds-find\">いまだ{_r('有効', 'ゆうこう')}な{_r('持続', 'じぞく')}{_r('陽圧', 'ようあつ')}{_r('呼吸', 'こきゅう')}{_r('療法', 'りょうほう')}が"
            f"{_r('導入', 'どうにゅう')}されていない</strong>{_r('成人', 'せいじん')}においては、"
            f"<strong class=\"cds-int\">ベンゾジアゼピン{_r('系', 'けい')}{_r('薬剤', 'やくざい')}</strong>"
            f"およびその{_r('他', 'た')}の{_r('中枢', 'ちゅうすう')}{_r('神経', 'しんけい')}{_r('抑制薬', 'よくせいやく')}の{_r('使用', 'しよう')}は"
            f"<strong class=\"cds-con\">{_r('原則', 'げんそく')}{_r('禁忌', 'きんき')}</strong>"
            f"とする。これらの{_r('薬剤', 'やくざい')}は{_r('上気道', 'じょうきどう')}{_r('拡張筋', 'かくちょうきん')}の{_r('緊張', 'きんちょう')}を{_r('低下', 'ていか')}させ、"
            f"{_r('低酸素血症', 'ていさんそけっしょう')}および{_r('高炭酸血症', 'こうたんさんけっしょう')}に{_r('対', 'たい')}する{_r('覚醒', 'かくせい')}{_r('反応', 'はんのう')}を{_r('鈍化', 'どんか')}させ、"
            f"{_r('無呼吸', 'むこきゅう')}の{_r('遷延化', 'せんえんか')}、{_r('著明', 'ちょめい')}な{_r('酸素', 'さんそ')}{_r('飽和度', 'ほうわど')}{_r('低下', 'ていか')}、ならびに{_r('致死的', 'ちしてき')}な"
            f"{_r('夜間', 'やかん')}{_r('呼吸不全', 'こきゅうふぜん')}リスクの{_r('著', 'いちじる')}しい{_r('上昇', 'じょうしょう')}と{_r('関連', 'かんれん')}する"
            f"（{_r('推奨度', 'すいしょうど')} 2、エビデンスレベル B ── {_r('害', 'がい')}）。"
        ),
    ),
    lean_filename="ScenarioC.lean",
    lean_subdir="ja",
    audit_summary=(
        f"{_r('上記', 'じょうき')}の Lean 4 {_r('形式化', 'けいしきか')}は、{_r('日本', 'にほん')}{_r('不安', 'ふあん')}{_r('症', 'しょう')}{_r('学会', 'がっかい')}・{_r('日本', 'にほん')}{_r('神経', 'しんけい')}{_r('精神', 'せいしん')}{_r('薬理', 'やくり')}{_r('学会', 'がっかい')}"
        f"『パニック{_r('症', 'しょう')}の{_r('診療', 'しんりょう')}ガイドライン（2025{_r('年版', 'ねんばん')}）』の "
        f"<code>«{_r('不安', 'ふあん')}{_r('症', 'しょう')}{_r('神経', 'しんけい')}{_r('精神', 'せいしん')}{_r('薬理', 'やくり')}パニック{_r('症', 'しょう')}2025_{_r('急性期', 'きゅうせいき')}»</code> {_r('公理', 'こうり')}と{_r('日本', 'にほん')}{_r('呼吸器', 'こきゅうき')}{_r('学会', 'がっかい')}"
        f"『{_r('睡眠時', 'すいみんじ')}{_r('無呼吸', 'むこきゅう')}{_r('症候群', 'しょうこうぐん')}（SAS）の{_r('診療', 'しんりょう')}ガイドライン2020』の "
        f"<code>«{_r('呼吸器', 'こきゅうき')}SAS2020_BZD»</code> {_r('公理', 'こうり')}から "
        f"<code>«{_r('適応', 'てきおう')}» «{_r('田中', 'たなか')}{_r('一郎', 'いちろう')}» «{_r('治療', 'ちりょう')}».«ベンゾジアゼピン» \u2227 "
        f"«{_r('禁忌', 'きんき')}» «{_r('田中', 'たなか')}{_r('一郎', 'いちろう')}» «{_r('治療', 'ちりょう')}».«ベンゾジアゼピン»</code> を"
        f"{_r('証明', 'しょうめい')}し、<code>«{_r('治療法', 'ちりょうほう')}の{_r('両立', 'りょうりつ')}{_r('不能性', 'ふのうせい')}»</code> を{_r('介', 'かい')}して "
        f"<code>False</code> を{_r('導出', 'どうしゅつ')}します。{_r('本', 'ほん')}{_r('監査', 'かんさ')}は、{_r('未', 'み')}{_r('治療', 'ちりょう')}の{_r('重症', 'じゅうしょう')} OSA に"
        f"おいて{_r('日本', 'にほん')}のパニック{_r('症', 'しょう')}ガイドライン{_r('推奨', 'すいしょう')}が{_r('引', 'ひ')}き{_r('起', 'お')}こす{_r('文字通', 'もじどお')}りの"
        f"{_r('衝突', 'しょうとつ')}を{_r('可視化', 'かしか')}します。"
    ),
    plain_english=(
        f"{_r('本', 'ほん')}システムは、{_r('終夜', 'しゅうや')}{_r('睡眠', 'すいみん')}ポリグラフ{_r('検査', 'けんさ')}で{_r('確定', 'かくてい')}された{_r('重症', 'じゅうしょう')}{_r('閉塞性', 'へいそくせい')}"
        f"{_r('睡眠時', 'すいみんじ')}{_r('無呼吸', 'むこきゅう')}を{_r('有', 'ゆう')}し、{_r('未', 'いま')}だ CPAP {_r('療法', 'りょうほう')}が{_r('導入', 'どうにゅう')}されていないこの58{_r('歳', 'さい')}の"
        f"{_r('患者', 'かんじゃ')}について、ガイドライン 1（{_r('急性', 'きゅうせい')}パニック{_r('発作', 'ほっさ')}に{_r('対', 'たい')}し{_r('短', 'たん')}{_r('時間', 'じかん')}{_r('作用', 'さよう')}{_r('型', 'がた')}"
        f"ベンゾジアゼピンの{_r('投与', 'とうよ')}を{_r('推奨', 'すいしょう')}する{_r('日本', 'にほん')}のパニック{_r('症', 'しょう')}{_r('診療', 'しんりょう')}ガイドライン）"
        f"とガイドライン 2（{_r('未', 'み')}{_r('治療', 'ちりょう')}{_r('重症', 'じゅうしょう')} OSA におけるベンゾジアゼピンを{_r('禁忌', 'きんき')}"
        f"とする{_r('日本', 'にほん')}{_r('呼吸器', 'こきゅうき')}{_r('学会', 'がっかい')} SAS {_r('診療', 'しんりょう')}ガイドライン2020）を{_r('同時', 'どうじ')}に{_r('遵守', 'じゅんしゅ')}する"
        f"ことが、「{_r('同一', 'どういつ')}の{_r('薬剤', 'やくざい')}を{_r('同一', 'どういつ')}{_r('患者', 'かんじゃ')}に{_r('対', 'たい')}し{_r('同時', 'どうじ')}に<em>{_r('適応', 'てきおう')}</em>かつ"
        f"<em>{_r('禁忌', 'きんき')}</em>とすることはできない」という{_r('基本', 'きほん')}{_r('原則', 'げんそく')}に{_r('違反', 'いはん')}せずには"
        f"{_r('不可能', 'ふかのう')}であることを{_r('数学的', 'すうがくてき')}に{_r('証明', 'しょうめい')}しました。"
    ),
)


# ---------------------------------------------------------------------------
# Public registry.
# ---------------------------------------------------------------------------

SCENARIOS_BY_LOCALE: dict[str, dict[str, Scenario]] = {
    "ja": {
        _JA_SCENARIO_A.id: _JA_SCENARIO_A,
        _JA_SCENARIO_B.id: _JA_SCENARIO_B,
        _JA_SCENARIO_C.id: _JA_SCENARIO_C,
    },
    "en": {
        _EN_SCENARIO_A.id: _EN_SCENARIO_A,
        _EN_SCENARIO_B.id: _EN_SCENARIO_B,
        _EN_SCENARIO_C.id: _EN_SCENARIO_C,
    },
}


def get_scenarios(locale: str) -> dict[str, Scenario]:
    """Return the scenario registry for ``locale`` (defaults to JA on miss)."""
    return SCENARIOS_BY_LOCALE[normalize_locale(locale)]


# Backwards-compatible alias used by the precompile path: any locale's
# registry will resolve the same Lean filenames, so we expose the default.
SCENARIOS: dict[str, Scenario] = SCENARIOS_BY_LOCALE[DEFAULT_LOCALE]
