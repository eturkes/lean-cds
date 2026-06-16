"""Per-locale gloss table for every MedicalKnowledge symbol. Single source of truth for tooltip prose; EN talks AHA/KDIGO/ADA/APA/AASM with English glosses, JA talks JSH/JSN/JDS/JSAD/JRS with Japanese glosses. Universal Lean identifiers (e.g. ``HasEssentialHypertension``) share keys across locales but their ``reads`` text is translated."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from i18n import normalize_locale


# Symbol roles. A phrase tooltip is composed differently depending on
# what kind of symbol heads the phrase.
ROLE_PATIENT_TYPE = "patient_type"  # `Patient`
ROLE_TREATMENT_CTOR = "treatment_ctor"  # `Treatment.thiazideDiuretic`
ROLE_PROPOSITION = "proposition"  # `False`
ROLE_CONDITION_PRED = "condition_pred"  # `HasEssentialHypertension`
ROLE_DEONTIC_PRED = "deontic_pred"  # `Indicated`, `Contraindicated`
ROLE_COLLISION_DEF = "collision_def"  # `Collision` (a `def`, not a pred)
ROLE_GUIDELINE_AXIOM = "guideline_axiom"  # `JSH2019_Ch5_FirstLine`, etc.
ROLE_GLOBAL_AXIOM = "global_axiom"  # `incompatible_modalities`
ROLE_AND_INTRO = "and_intro"  # `And.intro`


@dataclass(frozen=True)
class VocabEntry:
    """One MedicalKnowledge symbol's tooltip prose. Fields:
    - ``plain``: atomic noun phrase when mentioned but not applied (e.g. "the AHA/ACC hypertension guideline").
    - ``reads``: reading when applied to args (e.g. ``HasEssentialHypertension p`` → "has essential hypertension").
    - ``shape``: Lean type signature for fallback reference.
    - ``source``: real-world publication encoded (only for ``ROLE_GUIDELINE_AXIOM``).
    - ``noun``: treatment-constructor reading as deontic-predicate arg (e.g. "a thiazide diuretic").
    """

    role: str
    plain: str
    reads: str = ""
    shape: str = ""
    source: str = ""
    noun: str = ""


# English (American clinical guidelines).

_EN_VOCAB: dict[str, VocabEntry] = {
    # ---- Types / constants -------------------------------------------
    "Patient": VocabEntry(
        role=ROLE_PATIENT_TYPE,
        plain="the opaque `Patient` type",
        noun="a patient",
    ),
    "Treatment.thiazideDiuretic": VocabEntry(
        role=ROLE_TREATMENT_CTOR,
        plain="the `thiazideDiuretic` constructor of the `Treatment` enum",
        noun="a thiazide diuretic",
    ),
    "Treatment.ivRegularInsulin": VocabEntry(
        role=ROLE_TREATMENT_CTOR,
        plain="the `ivRegularInsulin` constructor of the `Treatment` enum",
        noun="IV regular insulin",
    ),
    "Treatment.benzodiazepine": VocabEntry(
        role=ROLE_TREATMENT_CTOR,
        plain="the `benzodiazepine` constructor of the `Treatment` enum",
        noun="a short-acting benzodiazepine",
    ),
    "False": VocabEntry(
        role=ROLE_PROPOSITION,
        plain="`False`: the proposition that is never true",
    ),
    # ---- Condition predicates (Patient → Prop) -----------------------
    "HasEssentialHypertension": VocabEntry(
        role=ROLE_CONDITION_PRED,
        plain="the condition predicate `HasEssentialHypertension`",
        reads="has a confirmed diagnosis of essential hypertension",
        shape="Patient → Prop",
    ),
    "HasSevereDehydration": VocabEntry(
        role=ROLE_CONDITION_PRED,
        plain="the condition predicate `HasSevereDehydration`",
        reads="shows clinical evidence of severe dehydration",
        shape="Patient → Prop",
    ),
    "HasDiabeticKetoacidosis": VocabEntry(
        role=ROLE_CONDITION_PRED,
        plain="the condition predicate `HasDiabeticKetoacidosis`",
        reads="meets DKA criteria",
        shape="Patient → Prop",
    ),
    "HasSerumPotassiumGE33": VocabEntry(
        role=ROLE_CONDITION_PRED,
        plain="the condition predicate `HasSerumPotassiumGE33`",
        reads="has serum K⁺ at least 3.5 mEq/L",
        shape="Patient → Prop",
    ),
    "HasSevereHypokalemia": VocabEntry(
        role=ROLE_CONDITION_PRED,
        plain="the condition predicate `HasSevereHypokalemia`",
        reads="has severe hypokalaemia (serum K⁺ below 3.5 mEq/L)",
        shape="Patient → Prop",
    ),
    "HasAcutePanicEpisode": VocabEntry(
        role=ROLE_CONDITION_PRED,
        plain="the condition predicate `HasAcutePanicEpisode`",
        reads="is presenting in an acute, debilitating panic episode",
        shape="Patient → Prop",
    ),
    "HasUntreatedSevereOSA": VocabEntry(
        role=ROLE_CONDITION_PRED,
        plain="the condition predicate `HasUntreatedSevereOSA`",
        reads=(
            "has polysomnography-confirmed severe obstructive sleep "
            "apnoea and is not yet on positive airway pressure therapy"
        ),
        shape="Patient → Prop",
    ),
    # ---- Deontic predicates (Patient → Treatment → Prop) -------------
    "Indicated": VocabEntry(
        role=ROLE_DEONTIC_PRED,
        plain="the deontic predicate `Indicated`",
        reads="is indicated for",
        shape="Patient → Treatment → Prop",
    ),
    "Contraindicated": VocabEntry(
        role=ROLE_DEONTIC_PRED,
        plain="the deontic predicate `Contraindicated`",
        reads="is contraindicated for",
        shape="Patient → Treatment → Prop",
    ),
    "Collision": VocabEntry(
        role=ROLE_COLLISION_DEF,
        plain="the `Collision` def",
        reads="is simultaneously indicated AND contraindicated for",
        shape="Patient → Treatment → Prop  := Indicated p t ∧ Contraindicated p t",
    ),
    # ---- Guideline axioms (American sources) -------------------------
    "AHA_ACC_HTN_8_1_6": VocabEntry(
        role=ROLE_GUIDELINE_AXIOM,
        plain="the AHA/ACC hypertension guideline §8.1.6 axiom",
        reads=(
            "if a patient has essential hypertension, a thiazide diuretic "
            "is indicated for them"
        ),
        shape=(
            "∀ p, HasEssentialHypertension p → "
            "Indicated p Treatment.thiazideDiuretic"
        ),
        source="AHA/ACC Hypertension Guideline §8.1.6",
    ),
    "KDIGO_AKI_3_4": VocabEntry(
        role=ROLE_GUIDELINE_AXIOM,
        plain="the KDIGO Acute Kidney Injury guideline §3.4 axiom",
        reads=(
            "if a patient has severe dehydration, any diuretic is "
            "contraindicated for them"
        ),
        shape=(
            "∀ p, HasSevereDehydration p → "
            "Contraindicated p Treatment.thiazideDiuretic"
        ),
        source="KDIGO AKI Guideline §3.4",
    ),
    "ADA_DKA_Sec16": VocabEntry(
        role=ROLE_GUIDELINE_AXIOM,
        plain="the ADA Standards of Care §16 axiom",
        reads=(
            "if a patient is in DKA, IV regular insulin is indicated "
            "for them"
        ),
        shape=(
            "∀ p, HasDiabeticKetoacidosis p → "
            "Indicated p Treatment.ivRegularInsulin"
        ),
        source="ADA Standards of Care §16",
    ),
    "ADA_DKA_Sec16_KSafety": VocabEntry(
        role=ROLE_GUIDELINE_AXIOM,
        plain="the ADA DKA potassium-safety axiom",
        reads=(
            "if a patient has severe hypokalaemia, insulin is "
            "contraindicated for them"
        ),
        shape=(
            "∀ p, HasSevereHypokalemia p → "
            "Contraindicated p Treatment.ivRegularInsulin"
        ),
        source="ADA Standards of Care §16, DKA Potassium Management",
    ),
    "APA_Panic_Acute": VocabEntry(
        role=ROLE_GUIDELINE_AXIOM,
        plain="the APA panic-disorder guideline axiom",
        reads=(
            "if a patient is in an acute panic episode, a short-acting "
            "benzodiazepine is indicated for them"
        ),
        shape=(
            "∀ p, HasAcutePanicEpisode p → "
            "Indicated p Treatment.benzodiazepine"
        ),
        source="APA Panic Disorder Practice Guideline",
    ),
    "AASM_OSA_PharmSafety": VocabEntry(
        role=ROLE_GUIDELINE_AXIOM,
        plain="the AASM OSA pharmacologic-safety axiom",
        reads=(
            "if a patient has untreated severe obstructive sleep "
            "apnoea, benzodiazepines are contraindicated for them"
        ),
        shape=(
            "∀ p, HasUntreatedSevereOSA p → "
            "Contraindicated p Treatment.benzodiazepine"
        ),
        source="AASM Adult OSA Guideline, Pharmacologic Safety Statement",
    ),
    # ---- Global axioms / constructors --------------------------------
    "incompatible_modalities": VocabEntry(
        role=ROLE_GLOBAL_AXIOM,
        plain="the `incompatible_modalities` axiom",
        reads=(
            "no treatment can be simultaneously indicated and "
            "contraindicated for the same patient"
        ),
        shape="∀ p t, ¬ (Indicated p t ∧ Contraindicated p t)",
    ),
    "And.intro": VocabEntry(
        role=ROLE_AND_INTRO,
        plain="Lean's `And.intro` constructor",
        reads=(
            "to prove a conjunction `P ∧ Q`, supply a proof of `P` and "
            "a proof of `Q` separately"
        ),
    ),
}


# Japanese (Japanese clinical guidelines).

_JA_VOCAB: dict[str, VocabEntry] = {
    # ---- Types / constants -------------------------------------------
    "«患者»": VocabEntry(
        role=ROLE_PATIENT_TYPE,
        plain="不透明な `«患者»` 型",
        noun="患者",
    ),
    "«治療».«サイアザイド系利尿薬»": VocabEntry(
        role=ROLE_TREATMENT_CTOR,
        plain="`«治療»` 列挙体の `«サイアザイド系利尿薬»` コンストラクタ",
        noun="サイアザイド系利尿薬",
    ),
    "«治療».«速効型インスリン静注»": VocabEntry(
        role=ROLE_TREATMENT_CTOR,
        plain="`«治療»` 列挙体の `«速効型インスリン静注»` コンストラクタ",
        noun="速効型インスリン静注",
    ),
    "«治療».«ベンゾジアゼピン»": VocabEntry(
        role=ROLE_TREATMENT_CTOR,
        plain="`«治療»` 列挙体の `«ベンゾジアゼピン»` コンストラクタ",
        noun="短時間作用型ベンゾジアゼピン",
    ),
    "False": VocabEntry(
        role=ROLE_PROPOSITION,
        plain="`False`：決して真にならない命題",
    ),
    # ---- Condition predicates («患者» → Prop) ------------------------
    "«本態性高血圧を有する»": VocabEntry(
        role=ROLE_CONDITION_PRED,
        plain="病態述語 `«本態性高血圧を有する»`",
        reads="本態性高血圧の確定診断を有する",
        shape="«患者» → Prop",
    ),
    "«重症脱水を呈する»": VocabEntry(
        role=ROLE_CONDITION_PRED,
        plain="病態述語 `«重症脱水を呈する»`",
        reads="重症脱水の臨床所見を呈する",
        shape="«患者» → Prop",
    ),
    "«糖尿病性ケトアシドーシスを呈する»": VocabEntry(
        role=ROLE_CONDITION_PRED,
        plain="病態述語 `«糖尿病性ケトアシドーシスを呈する»`",
        reads="DKA の診断基準を満たす",
        shape="«患者» → Prop",
    ),
    "«血清カリウム3_3以上»": VocabEntry(
        role=ROLE_CONDITION_PRED,
        plain="病態述語 `«血清カリウム3_3以上»`",
        reads="血清 K⁺ が 3.3 mEq/L 以上である",
        shape="«患者» → Prop",
    ),
    "«重症低カリウム血症を呈する»": VocabEntry(
        role=ROLE_CONDITION_PRED,
        plain="病態述語 `«重症低カリウム血症を呈する»`",
        reads="重症低カリウム血症（血清 K⁺ < 3.3 mEq/L）を呈する",
        shape="«患者» → Prop",
    ),
    "«急性パニック発作を呈する»": VocabEntry(
        role=ROLE_CONDITION_PRED,
        plain="病態述語 `«急性パニック発作を呈する»`",
        reads="急性かつ重度のパニック発作を呈している",
        shape="«患者» → Prop",
    ),
    "«未治療の重症閉塞性睡眠時無呼吸を有する»": VocabEntry(
        role=ROLE_CONDITION_PRED,
        plain="病態述語 `«未治療の重症閉塞性睡眠時無呼吸を有する»`",
        reads=(
            "終夜睡眠ポリグラフ検査で確定された重症閉塞性睡眠時無呼吸を"
            "有し、未だ持続陽圧呼吸（CPAP）療法が導入されていない"
        ),
        shape="«患者» → Prop",
    ),
    # ---- Deontic predicates («患者» → «治療» → Prop) -----------------
    "«適応»": VocabEntry(
        role=ROLE_DEONTIC_PRED,
        plain="義務論的述語 `«適応»`",
        reads="に対して適応される",
        shape="«患者» → «治療» → Prop",
    ),
    "«禁忌»": VocabEntry(
        role=ROLE_DEONTIC_PRED,
        plain="義務論的述語 `«禁忌»`",
        reads="に対して禁忌である",
        shape="«患者» → «治療» → Prop",
    ),
    "«衝突»": VocabEntry(
        role=ROLE_COLLISION_DEF,
        plain="`«衝突»` 定義",
        reads="に対して同時に適応かつ禁忌である",
        shape="«患者» → «治療» → Prop  := «適応» p t ∧ «禁忌» p t",
    ),
    # ---- Guideline axioms (Japanese sources) -------------------------
    "«高血圧2019_第5章_第一選択»": VocabEntry(
        role=ROLE_GUIDELINE_AXIOM,
        plain="日本高血圧学会『高血圧治療ガイドライン2019』第5章の公理",
        reads=(
            "本態性高血圧を有する患者に対し、サイアザイド系利尿薬を"
            "第一選択降圧薬として適応する"
        ),
        shape=(
            "∀ p, «本態性高血圧を有する» p → "
            "«適応» p «治療».«サイアザイド系利尿薬»"
        ),
        source="日本高血圧学会『高血圧治療ガイドライン2019』第5章",
    ),
    "«腎臓AKI2016_利尿薬»": VocabEntry(
        role=ROLE_GUIDELINE_AXIOM,
        plain="日本腎臓学会ほか『AKI 診療ガイドライン2016』の利尿薬公理",
        reads=(
            "重症脱水を呈する患者に対しては、いかなる利尿薬の投与も"
            "禁忌とする"
        ),
        shape=(
            "∀ p, «重症脱水を呈する» p → "
            "«禁忌» p «治療».«サイアザイド系利尿薬»"
        ),
        source="日本腎臓学会『AKI 診療ガイドライン2016』",
    ),
    "«糖尿病2024_第20_1項_DKA»": VocabEntry(
        role=ROLE_GUIDELINE_AXIOM,
        plain="日本糖尿病学会『糖尿病診療ガイドライン2024』第20-1項 DKA 公理",
        reads=(
            "DKA を呈する患者に対し、速効型インスリンの持続静注を"
            "速やかに開始する"
        ),
        shape=(
            "∀ p, «糖尿病性ケトアシドーシスを呈する» p → "
            "«適応» p «治療».«速効型インスリン静注»"
        ),
        source="日本糖尿病学会『糖尿病診療ガイドライン2024』第20-1項",
    ),
    "«糖尿病2024_第20_1項_K管理»": VocabEntry(
        role=ROLE_GUIDELINE_AXIOM,
        plain="同ガイドライン第20-1項の血清カリウム管理公理",
        reads=(
            "重症低カリウム血症（血清 K⁺ < 3.3 mEq/L）を呈する患者に"
            "対しては、インスリン投与を厳禁とする"
        ),
        shape=(
            "∀ p, «重症低カリウム血症を呈する» p → "
            "«禁忌» p «治療».«速効型インスリン静注»"
        ),
        source="日本糖尿病学会『糖尿病診療ガイドライン2024』第20-1項",
    ),
    "«不安症神経精神薬理パニック症2025_急性期»": VocabEntry(
        role=ROLE_GUIDELINE_AXIOM,
        plain=(
            "日本不安症学会・日本神経精神薬理学会『パニック症の診療"
            "ガイドライン（2025年版）』の急性期公理"
        ),
        reads=(
            "急性かつ重度のパニック発作を呈する患者に対し、短時間作用型"
            "ベンゾジアゼピンを第一選択薬物療法として適応する"
        ),
        shape=(
            "∀ p, «急性パニック発作を呈する» p → "
            "«適応» p «治療».«ベンゾジアゼピン»"
        ),
        source=(
            "日本不安症学会・日本神経精神薬理学会『パニック症の診療"
            "ガイドライン2025』"
        ),
    ),
    "«呼吸器SAS2020_BZD»": VocabEntry(
        role=ROLE_GUIDELINE_AXIOM,
        plain=(
            "日本呼吸器学会『睡眠時無呼吸症候群（SAS）の診療"
            "ガイドライン2020』の薬物療法安全公理"
        ),
        reads=(
            "未治療の中等症から重症閉塞性睡眠時無呼吸を有する患者に"
            "対しては、ベンゾジアゼピン系薬剤を原則禁忌とする"
        ),
        shape=(
            "∀ p, «未治療の重症閉塞性睡眠時無呼吸を有する» p → "
            "«禁忌» p «治療».«ベンゾジアゼピン»"
        ),
        source="日本呼吸器学会『SAS の診療ガイドライン2020』",
    ),
    # ---- Global axioms / constructors --------------------------------
    "«治療法の両立不能性»": VocabEntry(
        role=ROLE_GLOBAL_AXIOM,
        plain="`«治療法の両立不能性»` 公理",
        reads=(
            "同一の薬剤が同一患者に対して同時に適応かつ禁忌となることは"
            "あり得ない"
        ),
        shape="∀ p t, ¬ («適応» p t ∧ «禁忌» p t)",
    ),
    "And.intro": VocabEntry(
        role=ROLE_AND_INTRO,
        plain="Lean の `And.intro` コンストラクタ",
        reads=(
            "連言 `P ∧ Q` を証明するには、`P` の証明と `Q` の証明を"
            "それぞれ与える"
        ),
    ),
}


_VOCAB_BY_LOCALE: dict[str, dict[str, VocabEntry]] = {
    "en": _EN_VOCAB,
    "ja": _JA_VOCAB,
}


def lookup(symbol: str, locale: str = "en") -> Optional[VocabEntry]:
    """Vocab entry for an imported MedicalKnowledge symbol in ``locale``; ``None`` for locally-declared names (patients, observations, prior theorems) — callers fall back to a generic composition."""
    table = _VOCAB_BY_LOCALE[normalize_locale(locale)]
    return table.get(symbol)


def symbols_by_role(role: str, locale: str = "en") -> list[str]:
    """Identifiers in ``locale``'s vocab with ``role`` (insertion order). Lets the decorator recover locale-specific names without hard-coding e.g. ``"Patient"`` vs ``"«患者»"``."""
    table = _VOCAB_BY_LOCALE[normalize_locale(locale)]
    return [sym for sym, entry in table.items() if entry.role == role]
