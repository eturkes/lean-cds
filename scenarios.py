"""Per-locale scenario metadata registry. Whitelist-based ``id → ScenarioX.lean`` mapping; ``lean_subdir`` selects ``lean/{ja,en}/``. No user input is ever interpolated into Lean source — the host invokes ``lean`` on the static file referenced by the resolved id."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from i18n import normalize_locale

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


# English (American clinical guidelines).

_EN_SCENARIO_A = Scenario(
    id="scenario-a",
    title="Hypertension vs. Severe Dehydration",
    subtitle="Thiazide diuretic: indicated and contraindicated",
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
               "Evaluation, and Management of High Blood Pressure in Adults, "
               "Section 8.1.6 (Choice of Initial Medication)",
        body=(
            "In adults with confirmed "
            "<strong class=\"cds-cond\">essential hypertension</strong> and "
            "an estimated 10-year atherosclerotic cardiovascular disease "
            "risk of \u226510%, initiation of pharmacologic therapy with a "
            "<strong class=\"cds-int\">thiazide-type diuretic</strong> "
            "(chlorthalidone 12.5-25 mg orally once daily preferred) "
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
        source="KDIGO Clinical Practice Guideline for Acute Kidney Injury, "
               "Section 3.4 (Use of Diuretics in AKI)",
        body=(
            "In any patient exhibiting clinical evidence of "
            "<strong class=\"cds-cond\">severe dehydration</strong> ("
            "including frank "
            "<strong class=\"cds-find\">hypotension</strong>, "
            "<strong class=\"cds-find\">sinus tachycardia</strong>, "
            "<strong class=\"cds-find\">oliguria</strong> (&lt;0.5 mL/kg/h), "
            "an elevated "
            "<strong class=\"cds-find\">BUN-to-creatinine ratio</strong> "
            "(&gt;20:1), and laboratory or physical findings of end-organ "
            "hypoperfusion), the initiation or continuation of any "
            "<strong class=\"cds-int\">diuretic therapy</strong> is "
            "<strong class=\"cds-con\">contraindicated</strong>. "
            "Administration of diuretics in this hemodynamic context "
            "carries an unacceptable risk of precipitating circulatory "
            "collapse, ischemic acute kidney injury, and accelerated "
            "multi-organ dysfunction (Grade 1B: strong recommendation, "
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
    subtitle="Intravenous insulin: indicated and contraindicated",
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
        source="ADA Standards of Care in Diabetes, Section 16: "
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
        source="ADA Standards of Care in Diabetes, Section 16: "
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
            "level A: risk of harm)."
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
    subtitle="Benzodiazepine: indicated and contraindicated",
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
               "Panic Disorder, Acute Episode Management",
        body=(
            "For adults experiencing an "
            "<strong class=\"cds-cond\">acute, severe panic episode</strong> "
            "characterized by debilitating autonomic hyperarousal, "
            "depersonalization, and an impending sense of doom unresponsive "
            "to non-pharmacologic measures, "
            "<strong class=\"cds-int\">short-acting benzodiazepines</strong> "
            "(e.g., lorazepam 0.5-2 mg orally or intravenously) are "
            "<strong class=\"cds-ind\">indicated</strong> as recommended "
            "pharmacotherapy for rapid symptomatic relief and prevention of "
            "progression to a sustained anxiety crisis (APA recommendation "
            "category I, evidence level B)."
        ),
    ),
    guideline_b=Guideline(
        source="AASM Clinical Practice Guideline for the Treatment of Adult "
               "Obstructive Sleep Apnea, Sedative Avoidance Recommendation",
        body=(
            "In adults with a confirmed diagnosis of "
            "<strong class=\"cds-cond\">moderate-to-severe obstructive "
            "sleep apnea</strong> "
            "(<strong class=\"cds-find\">apnea-hypopnea index "
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


# Japanese (Japanese clinical guidelines).

_JA_SCENARIO_A = Scenario(
    id="scenario-a",
    title="高血圧症 対 重症脱水",
    subtitle="サイアザイド系利尿薬：適応かつ禁忌",
    patient_summary=(
        "15年来の<strong class=\"cds-cond\">本態性高血圧</strong>"
        "の既往を有する72歳の患者。急性胃腸炎に伴い救急外来を受診し、"
        "<strong class=\"cds-find\">低血圧</strong>（血圧 84/52 mmHg）、"
        "<strong class=\"cds-find\">頻脈</strong>、"
        "<strong class=\"cds-find\">乏尿</strong>、"
        "<strong class=\"cds-find\">BUN/Cr 比 28:1</strong>、"
        "ならびに<strong class=\"cds-cond\">重症脱水</strong>"
        "の臨床所見を呈している。"
    ),
    guideline_a=Guideline(
        source="日本高血圧学会『高血圧治療ガイドライン2019（JSH2019）』"
               "第5章「降圧薬」積極的適応のない高血圧の第一選択薬",
        body=(
            "確定診断された<strong class=\"cds-cond\">本態性高血圧</strong>"
            "を有する成人で、積極的適応がない場合、"
            "<strong class=\"cds-int\">サイアザイド系利尿薬</strong>"
            "（少量投与を原則とする）は、Ca拮抗薬および ARB／ACE 阻害薬と"
            "並ぶ第一選択降圧薬として"
            "<strong class=\"cds-ind\">適応</strong>される"
            "（推奨グレード A、エビデンスレベル I）。本ガイドラインは、"
            "食塩摂取量の多い日本人集団および高齢者において"
            "<strong class=\"cds-int\">サイアザイド系利尿薬</strong>"
            "の有用性が高いことを明記しており、長期血圧管理において"
            "ガイドラインに基づく薬物療法の中核を担う。"
        ),
    ),
    guideline_b=Guideline(
        source="日本腎臓学会ほか合同『AKI（急性腎障害）診療ガイドライン2016』"
               "第3章 CQ「利尿薬の AKI 予防・治療における推奨」",
        body=(
            "<strong class=\"cds-cond\">重症脱水</strong>"
            "の臨床的所見、すなわち明らかな"
            "<strong class=\"cds-find\">低血圧</strong>、"
            "<strong class=\"cds-find\">洞性頻脈</strong>、"
            "<strong class=\"cds-find\">乏尿</strong>"
            "（&lt;0.5 mL/kg/時）、"
            "<strong class=\"cds-find\">BUN/Cr 比の上昇</strong>"
            "（&gt;20:1）、ならびに末梢臓器灌流低下を示す検査・身体所見"
            "を呈する患者においては、いかなる"
            "<strong class=\"cds-int\">利尿薬療法</strong>"
            "の開始または継続も"
            "<strong class=\"cds-con\">絶対禁忌</strong>"
            "である。本ガイドラインは、まず十分な輸液による容量補正を"
            "行うことを推奨し、AKI の予防および治療目的での利尿薬投与は"
            "推奨しない。本血行動態下での利尿薬投与は、循環虚脱、"
            "虚血性急性腎障害、ならびに多臓器不全進行の容認できない"
            "リスクを伴う（推奨度 1、エビデンスレベル B）。"
        ),
    ),
    lean_filename="ScenarioA.lean",
    lean_subdir="ja",
    audit_summary=(
        "上記の Lean 4 形式化は、<code>«高血圧2019_第5章_第一選択»</code> と "
        "<code>«腎臓AKI2016_利尿薬»</code> の公理から "
        "<code>«適応» «山田太郎» «治療».«サイアザイド系利尿薬» \u2227 "
        "«禁忌» «山田太郎» «治療».«サイアザイド系利尿薬»</code> を"
        "証明し、<code>«治療法の両立不能性»</code> を介して "
        "<code>False</code> を導出します。カーネルが信頼する公理リストは、"
        "矛盾に関与したガイドラインと患者所見の正確な集合です。"
    ),
    plain_english=(
        "本システムは、この72歳の患者について、ガイドライン 1（本態性"
        "高血圧に対しサイアザイド系利尿薬を第一選択薬として推奨する"
        "JSH2019 第5章）とガイドライン 2（重症脱水においていかなる利尿薬"
        "投与も推奨しない JSN AKI 診療ガイドライン2016）を同時に遵守する"
        "ことが、「同一の薬剤を同一患者に対し同時に<em>適応</em>かつ"
        "<em>禁忌</em>とすることはできない」という基本原則に違反せずには"
        "不可能であることを数学的に証明しました。"
    ),
)


_JA_SCENARIO_B = Scenario(
    id="scenario-b",
    title="糖尿病性ケトアシドーシス 対 重症低カリウム血症",
    subtitle="経静脈インスリン：適応かつ禁忌",
    patient_summary=(
        "1型糖尿病を有する34歳の患者。多尿、Kussmaul 呼吸、"
        "<strong class=\"cds-find\">血漿グルコース 612 mg/dL</strong>、"
        "<strong class=\"cds-find\">動脈血 pH 7.18</strong>、"
        "<strong class=\"cds-find\">血清重炭酸 9 mEq/L</strong>、"
        "アニオンギャップ 28、"
        "<strong class=\"cds-find\">中等度ケトン尿</strong>、"
        "ならびに測定値"
        "<strong class=\"cds-find\">血清カリウム 2.9 mEq/L</strong>"
        "を呈している。"
    ),
    guideline_a=Guideline(
        source="日本糖尿病学会『糖尿病診療ガイドライン2024』"
               "第20-1項「糖尿病性ケトアシドーシスの診断と治療」",
        body=(
            "<strong class=\"cds-cond\">糖尿病性ケトアシドーシス</strong>"
            "（<strong class=\"cds-find\">血漿グルコース &gt;250 mg/dL</strong>、"
            "<strong class=\"cds-find\">動脈血 pH &lt;7.30</strong>、"
            "<strong class=\"cds-find\">血清重炭酸 &lt;18 mEq/L</strong>、"
            "ならびにケトン血症または"
            "<strong class=\"cds-find\">中等度以上のケトン尿</strong>"
            "の存在）の診断基準を満たす成人患者に対しては、"
            "<strong class=\"cds-int\">速効型インスリンの持続静注</strong>"
            "（0.1 単位/kg/時）の速やかな開始が、インスリン欠乏の補正、"
            "肝でのケトン体産生抑制、ならびに代謝性アシドーシスの改善を"
            "目的として"
            "<strong class=\"cds-ind\">適応</strong>される"
            "（推奨グレード A、エビデンスレベル 1）。"
            "<strong class=\"cds-cond\">DKA</strong> 診断基準が確認され次第、"
            "インスリン療法を遅延させてはならない。"
        ),
    ),
    guideline_b=Guideline(
        source="日本糖尿病学会『糖尿病診療ガイドライン2024』"
               "第20-1項 DKA 治療アルゴリズム「血清カリウム管理」",
        body=(
            "<strong class=\"cds-cond\">DKA</strong> を呈する患者で、"
            "<strong class=\"cds-find\">血清カリウム濃度が 3.3 mEq/L 未満</strong>"
            "と測定された症例においては、十分な経静脈カリウム補充により"
            "血清カリウムが 3.3 mEq/L 以上に回復するまで、"
            "<strong class=\"cds-int\">インスリン</strong>"
            "の投与は"
            "<strong class=\"cds-con\">厳禁</strong>"
            "とする。先行する"
            "<strong class=\"cds-cond\">低カリウム血症</strong>"
            "の状態下でインスリンが惹起する細胞内カリウム移動は、"
            "致死的な心室性不整脈、呼吸筋麻痺、ならびに心停止の差し迫った"
            "リスクを伴う（推奨グレード A、エビデンスレベル 1：害）。"
        ),
    ),
    lean_filename="ScenarioB.lean",
    lean_subdir="ja",
    audit_summary=(
        "上記の Lean 4 形式化は、日本糖尿病学会『糖尿病診療ガイドライン"
        "2024』第20-1項の DKA 適応公理 "
        "<code>«糖尿病2024_第20_1項_DKA»</code> と血清カリウム管理公理 "
        "<code>«糖尿病2024_第20_1項_K管理»</code> から "
        "<code>«適応» «鈴木花子» «治療».«速効型インスリン静注» \u2227 "
        "«禁忌» «鈴木花子» «治療».«速効型インスリン静注»</code> を"
        "証明し、<code>«治療法の両立不能性»</code> を介して "
        "<code>False</code> を導出します。インスリン適応公理を文字通り"
        "読むと K\u207a \u2265 3.3 mEq/L の前提条件が抜け落ちており、"
        "それこそが本監査が暴き出すよう設計された符号化バグです。"
    ),
    plain_english=(
        "本システムは、血清カリウム 2.9 mEq/L の糖尿病性ケトアシドーシス"
        "を呈するこの34歳の患者について、ガイドライン 1（DKA に対し速効型"
        "インスリン持続静注の開始を指示する『糖尿病診療ガイドライン2024』"
        "第20-1項）とガイドライン 2（血清カリウムが 3.3 mEq/L 未満の間は"
        "インスリン投与を厳禁とする同ガイドラインの血清カリウム管理項）を"
        "同時に遵守することが、「同一の薬剤を同一患者に対し同時に"
        "<em>適応</em>かつ<em>禁忌</em>とすることはできない」という基本原則"
        "に違反せずには不可能であることを数学的に証明しました。"
    ),
)


_JA_SCENARIO_C = Scenario(
    id="scenario-c",
    title="急性パニック症 対 重症閉塞性睡眠時無呼吸",
    subtitle="ベンゾジアゼピン：適応かつ禁忌",
    patient_summary=(
        "終夜睡眠ポリグラフ検査で確定診断された"
        "<strong class=\"cds-cond\">重症閉塞性睡眠時無呼吸</strong>"
        "（<strong class=\"cds-find\">無呼吸低呼吸指数 42 回/時</strong>、"
        "最低 SpO\u2082 78%）"
        "を有し<strong class=\"cds-find\">未だ持続陽圧呼吸（CPAP）療法"
        "が導入されていない</strong>58歳の患者。言語的鎮静に反応しない"
        "<strong class=\"cds-cond\">急性かつ重度のパニック発作</strong>"
        "を呈し救急外来を受診。"
    ),
    guideline_a=Guideline(
        source="日本不安症学会・日本神経精神薬理学会 合同『パニック症の"
               "診療ガイドライン（2025年版）』急性期薬物療法",
        body=(
            "成人における"
            "<strong class=\"cds-cond\">急性かつ重度のパニック発作</strong>"
            "（自律神経過活動、離人感、ならびに切迫した破局感を特徴と"
            "し、非薬物療法に反応しないもの）に対しては、"
            "<strong class=\"cds-int\">高力価ベンゾジアゼピン</strong>"
            "（例：ロラゼパム 0.5-2 mg 経口または静注、"
            "アルプラゾラム、クロナゼパム）が、迅速な症状緩和ならびに"
            "持続的な不安発作への進展予防のための第一選択薬物療法として"
            "<strong class=\"cds-ind\">適応</strong>される"
            "（推奨度 1、エビデンスレベル B）。SSRI の効果発現までの"
            "短期併用が標準的位置付けである。"
        ),
    ),
    guideline_b=Guideline(
        source="日本呼吸器学会『睡眠時無呼吸症候群（SAS）の診療"
               "ガイドライン2020』ベンゾジアゼピン使用に関する"
               "薬物療法安全声明",
        body=(
            "<strong class=\"cds-cond\">中等症から重症の閉塞性睡眠時無呼吸</strong>"
            "（<strong class=\"cds-find\">無呼吸低呼吸指数 \u226515 回/時</strong>）"
            "の確定診断を有し、"
            "<strong class=\"cds-find\">いまだ有効な持続陽圧呼吸療法が"
            "導入されていない</strong>成人においては、"
            "<strong class=\"cds-int\">ベンゾジアゼピン系薬剤</strong>"
            "およびその他の中枢神経抑制薬の使用は"
            "<strong class=\"cds-con\">原則禁忌</strong>"
            "とする。これらの薬剤は上気道拡張筋の緊張を低下させ、"
            "低酸素血症および高炭酸血症に対する覚醒反応を鈍化させ、"
            "無呼吸の遷延化、著明な酸素飽和度低下、ならびに致死的な"
            "夜間呼吸不全リスクの著しい上昇と関連する"
            "（推奨度 2、エビデンスレベル B：害）。"
        ),
    ),
    lean_filename="ScenarioC.lean",
    lean_subdir="ja",
    audit_summary=(
        "上記の Lean 4 形式化は、日本不安症学会・日本神経精神薬理学会"
        "『パニック症の診療ガイドライン（2025年版）』の "
        "<code>«不安症神経精神薬理パニック症2025_急性期»</code> 公理と日本呼吸器学会"
        "『睡眠時無呼吸症候群（SAS）の診療ガイドライン2020』の "
        "<code>«呼吸器SAS2020_BZD»</code> 公理から "
        "<code>«適応» «田中一郎» «治療».«ベンゾジアゼピン» \u2227 "
        "«禁忌» «田中一郎» «治療».«ベンゾジアゼピン»</code> を"
        "証明し、<code>«治療法の両立不能性»</code> を介して "
        "<code>False</code> を導出します。本監査は、未治療の重症 OSA に"
        "おいて日本のパニック症ガイドライン推奨が引き起こす文字通りの"
        "衝突を可視化します。"
    ),
    plain_english=(
        "本システムは、終夜睡眠ポリグラフ検査で確定された重症閉塞性"
        "睡眠時無呼吸を有し、未だ CPAP 療法が導入されていないこの58歳の"
        "患者について、ガイドライン 1（急性パニック発作に対し短時間作用型"
        "ベンゾジアゼピンの投与を推奨する日本のパニック症診療ガイドライン）"
        "とガイドライン 2（未治療重症 OSA におけるベンゾジアゼピンを禁忌"
        "とする日本呼吸器学会 SAS 診療ガイドライン2020）を同時に遵守する"
        "ことが、「同一の薬剤を同一患者に対し同時に<em>適応</em>かつ"
        "<em>禁忌</em>とすることはできない」という基本原則に違反せずには"
        "不可能であることを数学的に証明しました。"
    ),
)


# Public registry.

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
