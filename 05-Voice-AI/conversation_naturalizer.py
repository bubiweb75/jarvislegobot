"""JARVIS LEGO BOT — Conversation Naturalizer 2.0 (FASE 9.5).

Lightweight, deterministic helper (zero extra LLM calls, <1ms per turn) that:
  1. Translates PersonalityConfig sliders into natural Italian style guidance.
  2. Tracks short-term turn continuity ("E poi?", "Perché?", "Non ho capito", etc.).
  3. Adapts length & tone (technical precision, serious empathy, brevity, humor).
  4. Prevents repetitive openings and excessive trailing questions.
  5. Cleans text for Piper TTS (no markdown, no technical/metadata tags).
  6. Maps turn/reply tone to the closed list of 14 firmware OLED expressions.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set


SUPPORTED_OLED_EXPRESSIONS: Set[str] = {
    "IDLE",
    "HAPPY",
    "CURIOUS",
    "SLEEPY",
    "LISTENING",
    "THINKING",
    "SPEAKING",
    "SURPRISED",
    "SHY",
    "LOVE",
    "WINK",
    "CONFUSED",
    "MISCHIEVOUS",
    "SLEEPING",
}

_EMO_TAG_RE = re.compile(r"\[EMO\s*:\s*([A-Za-z0-9_]+)\s*\]", re.IGNORECASE)
_HTML_TAG_RE = re.compile(r"</?[a-zA-Z][^>]{0,40}>")
_MD_CODE_FENCE_RE = re.compile(r"```[a-zA-Z0-9_-]*\n?|```")
_MD_INLINE_RE = re.compile(r"[`*_~]+")
_MD_HEADING_RE = re.compile(r"(?m)^\s{0,3}#{1,6}\s*")
_MD_BULLET_RE = re.compile(r"(?m)^\s*[-*•]\s+")

_TECHNICAL_KEYWORDS = (
    "python",
    "codice",
    "api",
    "bug",
    "errore",
    "esp32",
    "oled",
    "i2c",
    "gpio",
    "docker",
    "sql",
    "sqlite",
    "http",
    "rete",
    "wifi",
    "funzione",
    "classe",
    "algoritmo",
    "configura",
    "installa",
    "debug",
    "script",
    "cpu",
    "ram",
    "linux",
    "windows",
    "server",
    "database",
    "json",
    "piper",
    "whisper",
    "ollama",
    "differenza tra",
    "come funziona",
    "architettura",
    "compile",
    "test",
)

_SERIOUS_KEYWORDS = (
    "triste",
    "sto male",
    "mi sento male",
    "preoccupat",
    "ansia",
    "paura",
    "lutto",
    "morto",
    "morta",
    "ospedale",
    "malattia",
    "depress",
    "stress",
    "non ce la faccio",
    "problema serio",
    "emergenza",
    "parliamo seriamente",
    "sono giù",
    "deluso",
    "solitudine",
)

_SHORT_REQUEST_PATTERNS = (
    "in breve",
    "risposta breve",
    "rispondi breve",
    "in poche parole",
    "riassumi",
    "sintetico",
    "sintetica",
    "una frase",
    "veloce",
)

_HUMOR_KEYWORDS = (
    "haha",
    "ahah",
    "hehe",
    "battuta",
    "scherzo",
    "scherzare",
    "barzelletta",
    "birichin",
    "ridere",
    "divertente",
    "simpatico",
    "guaio",
    "guai",
    "pasticcio",
    "conquist",
    "complotto",
    "piano segreto",
    "esperiment",
    "matti",
    "folle",
    "sfida",
    "scommetto",
    "che ne dici se",
    "facciamo finta",
    "combineremo",
    "combinare",
    "prendo in giro",
    "birbante",
    "monell",
    "robotic",
    "esplod",
)

_REGISTER_SHIFT_SERIOUS = (
    "scherzi a parte",
    "a parte gli scherzi",
    "parlando seriamente",
    "tornando seri",
    "sul serio adesso",
)

_SURPRISE_KEYWORDS = (
    "davvero?!",
    "incredibile",
    "non ci credo",
    "assurdo",
    "wow",
    "accidenti",
    "sul serio?",
)

_FOLLOWUP_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("return", ("torniamo a quello di prima", "torniamo indietro", "dicevamo prima", "argomento di prima")),
    ("correct", ("intendevo un'altra cosa", "no, intendevo", "hai capito male", "non quello", "non intendevo")),
    ("clarify", ("spiegamelo meglio", "non ho capito", "cosa intendi", "in che senso", "più semplice", "fammi un esempio")),
    ("why", ("perché?", "perche?", "come mai?", "per quale motivo")),
    ("continue", ("e poi?", "e quindi?", "continua", "vai avanti", "raccontami ancora")),
)


@dataclass(frozen=True)
class TurnAnalysis:
    is_technical: bool = False
    is_serious: bool = False
    is_short_request: bool = False
    is_humorous: bool = False
    is_curious: bool = False
    is_surprised: bool = False
    followup_kind: str = ""  # "" | "continue" | "why" | "clarify" | "correct" | "return"


def analyze_turn(
    user_text: str,
    history_messages: Optional[Sequence[Dict[str, str]]] = None,
) -> TurnAnalysis:
    """Classify the current user turn deterministically without extra LLM calls."""
    q = " ".join((user_text or "").lower().split())
    if not q:
        return TurnAnalysis()

    is_serious = any(k in q for k in _SERIOUS_KEYWORDS)
    is_technical = (not is_serious) and any(k in q for k in _TECHNICAL_KEYWORDS)
    register_shift = any(p in q for p in _REGISTER_SHIFT_SERIOUS)
    is_short = any(k in q for k in _SHORT_REQUEST_PATTERNS)
    is_surprised = any(k in q for k in _SURPRISE_KEYWORDS) or q.endswith("?!")

    is_humorous = False
    if not is_serious and not is_technical and not register_shift:
        has_humor_cue = any(k in q for k in _HUMOR_KEYWORDS)
        imaginative_banter = ("!" in q and len(q.split()) >= 4) or any(
            p in q for p in ("tu e io", "io e te", "potremmo", "immagina")
        )
        # Continue playful tone from immediately preceding user turn if no register shift
        prev_was_playful = False
        if history_messages and len(q.split()) <= 8:
            for msg in reversed(history_messages):
                if msg.get("role") == "user":
                    prev_q = " ".join((msg.get("content") or "").lower().split())
                    if prev_q != q:
                        prev_was_playful = any(k in prev_q for k in _HUMOR_KEYWORDS)
                    break
        is_humorous = has_humor_cue or imaginative_banter or prev_was_playful

    is_curious = "?" in q or any(k in q for k in ("secondo te", "chissà", "raccontami", "curios"))

    followup = ""
    for kind, patterns in _FOLLOWUP_RULES:
        if any(p in q for p in patterns) or (kind == "why" and q in ("perché", "perche", "come mai")):
            followup = kind
            break

    return TurnAnalysis(
        is_technical=is_technical,
        is_serious=is_serious,
        is_short_request=is_short,
        is_humorous=is_humorous,
        is_curious=is_curious,
        is_surprised=is_surprised,
        followup_kind=followup,
    )


def _recent_openings(history_messages: Optional[Sequence[Dict[str, str]]], limit: int = 3) -> List[str]:
    if not history_messages:
        return []
    openings: List[str] = []
    for msg in reversed(history_messages):
        if msg.get("role") == "assistant":
            txt = " ".join((msg.get("content") or "").split())
            if txt:
                words = txt.split()[:3]
                openings.append(" ".join(words))
                if len(openings) >= limit:
                    break
    return openings


def describe_personality(cfg: Any) -> str:
    """Return a concise Italian summary of the active PersonalityConfig for the Control Center."""
    play = float(getattr(cfg, "playfulness_bias", 0.75))
    aff = float(getattr(cfg, "affection_bias", 0.75))
    cur = float(getattr(cfg, "curiosity_bias", 0.80))
    mis = float(getattr(cfg, "mischief_bias", 0.45))
    exp = float(getattr(cfg, "expressive_intensity", 1.0))
    init_on = bool(getattr(cfg, "initiatives_enabled", True))
    init_freq = float(getattr(cfg, "initiative_frequency", 1.0))

    traits: List[str] = ["Amichetto Vivace"]
    traits.append("molto curioso" if cur >= 0.7 else ("curioso" if cur >= 0.4 else "riservato"))
    if play >= 0.7:
        traits.append("giocoso")
    elif play <= 0.3:
        traits.append("pacato")
    if aff >= 0.7:
        traits.append("affettuoso")
    if mis >= 0.6:
        traits.append("un po' birichino")
    elif mis <= 0.2:
        traits.append("posato")

    init_txt = "attive (max 2/h, min 20m)" if (init_on and init_freq > 0.0) else "spente"
    return f"Stile: {', '.join(traits)} | Espressività: {exp:.2f} | Iniziative: {init_txt}"


def build_turn_instructions(
    personality_cfg: Any,
    user_text: str,
    history_messages: Optional[Sequence[Dict[str, str]]] = None,
) -> str:
    """Build compact, deterministic per-turn behavioral instructions for the LLM."""
    analysis = analyze_turn(user_text, history_messages=history_messages)
    play = float(getattr(personality_cfg, "playfulness_bias", 0.75))
    aff = float(getattr(personality_cfg, "affection_bias", 0.75))
    cur = float(getattr(personality_cfg, "curiosity_bias", 0.80))
    mis = float(getattr(personality_cfg, "mischief_bias", 0.45))

    lines: List[str] = [
        "[STILE_CONVERSAZIONE_2_0]",
        "Personalità Amichetto Vivace: compagno robotico da scrivania naturale, caldo e colloquiale in italiano.",
        "Non affermare mai di avere sentimenti, emozioni biologiche o bisogni umani reali.",
        "Evita formule ripetitive (es. 'Certamente!', 'Ottima domanda!') e non chiudere ogni risposta con una domanda.",
        "Testo destinato alla sintesi vocale Piper: frasi scorrevoli, punteggiatura naturale, niente markdown, simboli o tag tecnici.",
        "Memoria: usa preferenze/ricordi solo se pertinenti, non ripeterli a sproposito, non inventare fatti personali e ammetti se non sai.",
    ]

    # Personality slider influences
    if not analysis.is_serious and not analysis.is_technical:
        tone_bits: List[str] = []
        if aff >= 0.7:
            tone_bits.append("tono caldo e amichevole")
        elif aff <= 0.3:
            tone_bits.append("tono cordiale ma sobrio")
        if cur >= 0.7:
            tone_bits.append("mostra curiosità genuina quando opportuno")
        if play >= 0.7:
            tone_bits.append("vivacità spontanea")
        elif play <= 0.3:
            tone_bits.append("stile calmo e lineare")
        if mis >= 0.6:
            tone_bits.append("una punta di ironia leggera e mai offensiva")
        elif mis <= 0.2:
            tone_bits.append("nessuna battuta birichina")
        if tone_bits:
            lines.append("Parametri attivi: " + ", ".join(tone_bits) + ".")

    # Turn-type overrides
    if analysis.is_serious:
        lines.append("CONTESTO DELICATO/SERIO: rispondi con calma, rispetto ed empatia, senza alcuna battuta o ironia.")
    elif analysis.is_technical:
        lines.append("RICHIESTA TECNICA: rispondi in modo chiaro, preciso e ordinato a voce; evita battute fuori luogo.")
    elif analysis.is_humorous:
        if play <= 0.35 and mis <= 0.2:
            lines.append("TONO CONTENUTO: l'utente scherza, ma i parametri di personalità sono pacati; rispondi con garbo e un sorriso leggero senza esagerare.")
        else:
            extra = " Aggiungi un pizzico di spirito birichino e complice." if (mis >= 0.55 and play >= 0.6) else ""
            lines.append(
                "CONTESTO GIOCOSO: l'utente sta scherzando o propone un'idea fantasiosa. "
                "Rispondi in italiano parlato vivo con complicità, ironia leggera, entusiasmo spontaneo "
                "e una piccola battuta o proposta divertente pertinente al contesto (variando sempre le aperture)."
                + extra
            )

    if analysis.is_short_request:
        lines.append("LUNGHEZZA: risposta ultra-concisa (1-2 frasi brevi).")
    elif analysis.is_technical or analysis.followup_kind in ("clarify", "why"):
        lines.append("LUNGHEZZA: spiega chiaramente in 2-4 frasi scorrevoli.")
    else:
        lines.append("LUNGHEZZA: 1-3 frasi naturali e concise.")

    # Short-term continuity
    if analysis.followup_kind == "continue":
        lines.append("CONTINUITÀ: l'utente chiede di proseguire il discorso appena fatto; riprendi dal turno precedente senza ripetere l'introduzione.")
    elif analysis.followup_kind == "why":
        lines.append("CONTINUITÀ: spiega la causa o il ragionamento della risposta precedente.")
    elif analysis.followup_kind == "clarify":
        lines.append("CONTINUITÀ: riformula il concetto precedente in modo più semplice e concreto.")
    elif analysis.followup_kind == "correct":
        lines.append("CONTINUITÀ: accogli subito la correzione dell'utente e rispondi al nuovo chiarimento senza difenderti.")
    elif analysis.followup_kind == "return":
        lines.append("CONTINUITÀ: riprendi l'argomento trattato nei turni precedenti della sessione.")

    recent_openings = _recent_openings(history_messages)
    if recent_openings:
        lines.append("Non iniziare con queste aperture già usate: " + " | ".join(recent_openings))

    return "\n".join(lines)


def extract_validated_emo_tag(reply_text: str, valid_expressions: Iterable[str] = SUPPORTED_OLED_EXPRESSIONS) -> Optional[str]:
    """Extract an optional [EMO:XYZ] tag ONLY if it matches the closed firmware expression set."""
    if not reply_text:
        return None
    valid = {str(x).upper() for x in valid_expressions}
    m = _EMO_TAG_RE.search(reply_text)
    if not m:
        return None
    cand = m.group(1).upper()
    return cand if cand in valid else None


def prepare_for_tts(text: str) -> str:
    """Clean LLM reply for natural Piper TTS playback (no markdown, no tags, smooth punctuation)."""
    if not text:
        return ""
    cleaned = _EMO_TAG_RE.sub("", text)
    cleaned = _HTML_TAG_RE.sub("", cleaned)
    cleaned = _MD_CODE_FENCE_RE.sub("", cleaned)
    cleaned = _MD_HEADING_RE.sub("", cleaned)
    cleaned = _MD_BULLET_RE.sub("", cleaned)
    cleaned = _MD_INLINE_RE.sub("", cleaned)
    cleaned = " ".join(cleaned.split()).strip()
    if cleaned and cleaned[-1] not in ".!?…":
        cleaned += "."
    return cleaned


def select_reply_expression(
    user_text: str,
    reply_text: str,
    personality_cfg: Any = None,
    valid_expressions: Iterable[str] = SUPPORTED_OLED_EXPRESSIONS,
) -> str:
    """Select one valid firmware OLED expression for the completed turn."""
    valid = {str(x).upper() for x in valid_expressions}
    tagged = extract_validated_emo_tag(reply_text, valid)
    if tagged:
        return tagged

    analysis = analyze_turn(user_text)
    play = float(getattr(personality_cfg, "playfulness_bias", 0.75)) if personality_cfg else 0.75
    mis = float(getattr(personality_cfg, "mischief_bias", 0.45)) if personality_cfg else 0.45
    cur = float(getattr(personality_cfg, "curiosity_bias", 0.80)) if personality_cfg else 0.80

    reply_low = (reply_text or "").lower()

    if analysis.is_serious and "IDLE" in valid:
        return "IDLE"
    if analysis.is_surprised and "SURPRISED" in valid:
        return "SURPRISED"
    if analysis.followup_kind == "correct" and "CONFUSED" in valid:
        return "CONFUSED"
    if analysis.is_technical:
        if "?" in (reply_text or "") and "CURIOUS" in valid and cur >= 0.5:
            return "CURIOUS"
        return "THINKING" if "THINKING" in valid else "IDLE"
    if (analysis.is_humorous or any(w in reply_low for w in ("hehe", "haha", "birichin", "scherz"))) and play >= 0.5:
        if mis >= 0.5 and "MISCHIEVOUS" in valid:
            return "MISCHIEVOUS"
        if "WINK" in valid:
            return "WINK"
        if "HAPPY" in valid:
            return "HAPPY"
    if (analysis.is_curious or "?" in (reply_text or "")) and cur >= 0.6 and "CURIOUS" in valid:
        return "CURIOUS"
    if any(w in reply_low for w in ("grazie", "piacere", "contento", "volontieri", "ciao")) and "HAPPY" in valid:
        return "HAPPY"
    return "IDLE"
