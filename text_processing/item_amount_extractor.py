import sys
from typing import Dict, Any, List, Optional

from spacy.matcher import DependencyMatcher, Matcher
from spacy.util import filter_spans
from text_to_num import text2num
import spacy
from utils.run_subprocess import exec_cmd

QAX=None

def get_query_amount_xtractor():
    global QAX
    if not QAX:
        QAX = QueryAmountExtractor()
    return QAX


class QueryAmountExtractor:
    SPACY_MODELS = {
        "de": "de_core_news_lg",
        "en": "en_core_web_lg"
    }

    def __init__(self, language: str = "de"):
        self.language = language.lower()
        if self.language not in self.SPACY_MODELS:
            raise ValueError(f"Sprache '{self.language}' wird nicht unterstützt.")

        self._nlp: Optional[spacy.language.Language] = None
        _ = self.nlp  # Lazy loading initialisieren

        self.matcher = self._build_item_matcher()
        self.dep_matcher = self._build_topic_dep_matcher()

    @property
    def nlp(self) -> spacy.language.Language:
        if self._nlp is None:
            model_name = self.SPACY_MODELS[self.language]
            try:
                self._nlp = spacy.load(model_name)
            except OSError:
                print(f"spaCy-Modell '{model_name}' missing. Install...")
                exec_cmd([sys.executable, "-m", "spacy", "download", model_name])
                self._nlp = spacy.load(model_name)
        return self._nlp

    def _build_item_matcher(self) -> Matcher:
        """Matcher für Menge + Nomen/Eigennamen (z.B. '5 ABC items', '33 test objekte')."""
        matcher = Matcher(self.nlp.vocab)
        # Strikt auf Substantive & Eigennamen beschränkt (Optional mit Adjektiv)
        pattern = [
            {"LIKE_NUM": True},
            {"POS": "ADJ", "OP": "?"},
            {"POS": {"IN": ["NOUN", "PROPN"]}, "OP": "+"}
        ]
        matcher.add("QUANTITY_ITEM", [pattern])
        return matcher

    def _build_topic_dep_matcher(self) -> DependencyMatcher:
        dep_matcher = DependencyMatcher(self.nlp.vocab)

        # Pattern für Präposition -> Head-Nomen -> Modifikator/Compound
        pattern_topic_phrase = [
            {
                "RIGHT_ID": "prep_anchor",
                "RIGHT_ATTRS": {
                    "POS": "ADP"  # Präposition (z. B. "über", "zum", "mit")
                }
            },
            {
                "LEFT_ID": "prep_anchor",
                "REL_OP": ">",
                "RIGHT_ID": "topic_head",
                "RIGHT_ATTRS": {
                    "POS": {"IN": ["NOUN", "PROPN"]}
                }
            },
            {
                "LEFT_ID": "topic_head",
                "REL_OP": ">",
                "RIGHT_ID": "topic_modifier",
                "RIGHT_ATTRS": {
                    # Erfasst Attribute, Compounds und Eigennamen (z.B. "ABC", "Terms", "service")
                    "DEP": {"IN": ["compound", "nk", "flat", "ag", "pobj"]},
                    "POS": {"IN": ["NOUN", "PROPN", "X"]}  # "X" fängt auch unbekannte Token / snake_case ab
                }
            }
        ]

        dep_matcher.add("DYNAMIC_TOPIC_DEP", [pattern_topic_phrase])
        return dep_matcher

    def _extract_subtree_lemmas(self, head_token: spacy.tokens.Token) -> List[str]:
        """Extrahiert alle inhaltstragenden Substantive/Eigennamen aus dem grammatikalischen Teilbaum."""
        tags = []
        for token in head_token.subtree:
            if token.pos_ in ("NOUN", "PROPN") and not token.is_stop and not token.is_punct:
                tags.append(token.lemma_)
        return list(dict.fromkeys(tags))


    def extract(
            self, text: str, valid_items: List[str] = None
    ) -> Dict[str, Any]:
        """
        Extrahiert Mengen, Items und Themen-Tags dynamisch aus der Texteingabe.

        :param valid_items: Optionale Liste bekannter/erwarteter Items zur
        Validierung (Performanz-/Item-Matching).
        """
        doc = self.nlp(text)
        valid_items_lower = (
            [item.lower() for item in valid_items] if valid_items else []
        )

        # 1. Item- & Mengenerkennung
        raw_matches = self.matcher(doc)
        spans = [doc[start:end] for _, start, end in raw_matches]
        filtered_spans = filter_spans(spans)

        items = {}
        matched_item_spans = []

        for span in filtered_spans:
            amount_raw = span[0].text
            try:
                amount = int(amount_raw)
            except ValueError:
                try:
                    amount = text2num(amount_raw, lang=self.language)
                except Exception:
                    amount = amount_raw

            # Item-Name extrahieren und lematisieren/normalisieren
            item_name = " ".join([token.text for token in span[1:]]).strip()
            item_lemma = " ".join(
                [token.lemma_.lower() for token in span[1:]]
            ).strip()

            #
            is_valid = True
            if valid_items_lower:
                is_valid = (
                        item_name.lower() in valid_items_lower
                        or item_lemma in valid_items_lower
                )

            if is_valid and item_name:
                items[item_name] = amount
                matched_item_spans.append(span)

        # 2. Themen- & Tag-Extraktion
        dep_matches = self.dep_matcher(doc)
        extracted_tags = []

        for match_id, token_ids in dep_matches:
            topic_head_token = doc[token_ids[1]]
            tags = self._extract_subtree_lemmas(topic_head_token)
            extracted_tags.extend(tags)

        # Fallback: Nutzen von Noun-Chunks & verbleibenden Tokens
        if not extracted_tags:
            for chunk in doc.noun_chunks:
                # Überprüfen, ob dieser Chunk Teil eines gültigen Items war
                overlap_with_items = any(
                    chunk.start < span.end and chunk.end > span.start
                    for span in matched_item_spans
                )

                if not overlap_with_items:
                    for token in chunk:
                        # Token-Filter: Nur Nomen/Namen, keine Stoppwörter und KEINE reinen Zahlen
                        if (
                                token.pos_ in ("NOUN", "PROPN", "X")
                                and not token.is_stop
                                and not token.like_num
                        ):
                            extracted_tags.append(token.lemma_)

        # Zusätzlicher Cleanup für Tags (Verhindert z.B. Zahlen oder Stoppwörter aus dep_matcher)
        cleaned_tags = []
        for tag in extracted_tags:
            tag_str = str(tag).strip()
            if tag_str and not tag_str.isdigit() and tag_str.lower() not in ("create", "tag", "tags"):
                cleaned_tags.append(tag_str)

        final_tags = list(dict.fromkeys(cleaned_tags))

        return {
            "items": items,
            "tags": final_tags,
            "llm_prompt_context": (
                f"Topics/Tags: {', '.join(final_tags)}" if final_tags else ""
            ),
        }

    def expand_queries_with_vectors(
            self,
            queries: List[str],
            min_sim: float = 0.66,
            target_pos: tuple = ("NOUN", "PROPN", "VERB")
    ) -> List[str]:
        """
        Erweitert Queries dynamisch um echte semantische Synonyme aus spaCy Vektoren.
        Durchläuft alle Top-50 Kandidaten vollständig zur Protokollierung.
        """
        expanded_queries = []

        for doc in self.nlp.pipe(queries):
            synonyms_found = []

            for token in doc:
                if (
                        token.pos_ in target_pos
                        and not token.is_stop
                        and not token.is_punct
                        and token.has_vector
                ):
                    vector = token.vector.reshape(1, -1)

                    # Top 50 ähnlichste Vektoren aus dem spaCy Vocab abrufen
                    ms = self.nlp.vocab.vectors.most_similar(vector, n=50)
                    target_hashes, _, similarities = ms

                    above_threshold = []
                    below_threshold = []

                    # Alle 50 Kandidaten durchlaufen (kein vorzeitiges break)
                    for target_hash, sim in zip(target_hashes[0], similarities[0]):
                        synonym_candidate = self.nlp.vocab.strings[target_hash]
                        candidate_lower = synonym_candidate.lower()
                        token_lower = token.text.lower()

                        # 1. Qualitative Filter (Wortstamm-, Selbst-Match- & Zeichen-Filter)
                        if (
                                candidate_lower == token_lower
                                or candidate_lower.startswith(token_lower[:4])
                                or not candidate_lower.isalnum()
                        ):
                            continue

                        # 2. Grammatikalische Filter (Wortart & Lemma-Check)
                        cand_doc = self.nlp(synonym_candidate)
                        if cand_doc and len(cand_doc) > 0:
                            cand_token = cand_doc[0]
                            cand_lemma = cand_token.lemma_.lower()

                            if (
                                    cand_token.pos_ in target_pos
                                    and cand_lemma != token.lemma_.lower()
                            ):
                                # 3. Nach Schwellenwert aufteilen
                                if sim >= min_sim:
                                    if cand_lemma not in above_threshold:
                                        above_threshold.append(cand_lemma)
                                else:
                                    if cand_lemma not in below_threshold and cand_lemma not in above_threshold:
                                        below_threshold.append(cand_lemma)

                    # Debug-Outputs für das aktuelle Token anzeigen
                    print(f"\n--- Token Evaluation: '{token.text}' ({token.pos_}) ---")
                    print(f"Above Threshold (>= {min_sim}): {above_threshold}")
                    print(f"Below Threshold (< {min_sim}):  {below_threshold}")

                    # Für die tatsächliche Erweiterung nur die 'above'-Synonyme bis max top_n_synonyms nutzen
                    synonyms_found.extend(above_threshold)

            # Duplikate entfernen unter Beibehaltung der Reihenfolge
            unique_synonyms = list(dict.fromkeys(synonyms_found))

            # RAG-optimierte Formatierung
            if unique_synonyms:
                synonym_str = " ".join(unique_synonyms)
                expanded_query = f"{doc.text} | Keywords: {synonym_str}"
            else:
                expanded_query = doc.text

            expanded_queries.append(expanded_query)

        return expanded_queries


if __name__ == "__main__":
    extractor = QueryAmountExtractor(language="en")

    sample_queries = [
        "Theme reporesents a web app that describes myself like a CV",
        "Fruit cerials and milk breakfast"
    ]

    print("\n--- 2. QUERY-ERWEITERUNG (en_core_web_lg Vektoren) ---")
    expanded_results = extractor.expand_queries_with_vectors(
        queries=sample_queries,
    )

    for orig, exp in zip(sample_queries, expanded_results):
        print(f"\nOriginal:  '{orig}'")
        print(f"Erweitert: '{exp}'")