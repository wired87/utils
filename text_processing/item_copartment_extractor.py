import re
import sys
from collections.abc import Callable
from typing import Any, Dict, Optional

import numpy as np
import spacy
from text_to_num import text2num

from oasismarket.settings import MODEL_PATH_REGISTRY
from utils.run_subprocess import exec_cmd

QCX = None


def get_compartment_xtractor():
    global QCX
    if not QCX:
        QCX = QuerySectionCompartmentExtractor()
    return QCX


class QuerySectionCompartmentExtractor:
    SPACY_MODELS = {
        "de": "de_core_news_lg",
        "en": "en_core_web_lg",
    }

    TARGET_SECTIONS = ["header", "main", "footer", "plugins"]
    SECTION_ALIASES = {
        "head": "header",
        "content": "main",
        "body": "main",
        "foot": "footer",
        "plugin": "plugins",
    }


    def __init__(self, language: str = "en", max_distance: int = 2):
        self.language = language.lower()
        if self.language not in self.SPACY_MODELS:
            raise ValueError(f"Sprache '{self.language}' wird nicht unterstützt.")

        self.max_distance = max_distance
        self._nlp: Optional[spacy.language.Language] = None
        _ = self.nlp

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

    def _tokenize(self, text: str) -> list[str]:
        """Tokenize a clause with the configured spaCy language model."""
        return [
            token.text
            for token in self.nlp(text)
            if not token.is_space and not token.is_punct
        ]

    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """Calculates Levenshtein edit distance between two strings for typo handling."""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)
        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    def _match_section_name(self, token_text: str) -> str | None:
        """Matches a token to a known section compartment accounting for typos."""
        clean_text = token_text.lower().strip()

        # Direct match
        if clean_text in self.TARGET_SECTIONS:
            return clean_text
        if clean_text in self.SECTION_ALIASES:
            return self.SECTION_ALIASES[clean_text]

        # Avoid fuzzy false positives such as "in" -> "main".
        if len(clean_text) < 4:
            return None

        # Fuzzy match via Levenshtein edit distance
        best_match = None
        min_dist = self.max_distance + 1

        for target in self.TARGET_SECTIONS:
            dist = self._levenshtein_distance(clean_text, target)
            if dist <= self.max_distance and dist < min_dist:
                min_dist = dist
                best_match = target

        return best_match

    def _parse_value(self, val_str: str) -> Any:
        """Parses a string into an integer or clean string item."""
        val_str = val_str.strip()
        try:
            return int(val_str)
        except ValueError:
            try:
                return text2num(val_str, lang=self.language)
            except Exception:
                return val_str

    def _parse_tokens(self, tokens: list[str]) -> list[Any]:
        values = []
        for token in tokens:
            if token.lower() in self.FILLER_WORDS:
                continue
            value = self._parse_value(token)
            if isinstance(value, int) or (isinstance(value, str) and value):
                values.append(value)
        return values

    @staticmethod
    def _normalized_matrix(values: Any) -> np.ndarray | None:
        matrix = np.asarray(values, dtype=np.float64)
        if matrix.ndim == 1:
            matrix = matrix[np.newaxis, :]
        if matrix.ndim != 2 or matrix.size == 0:
            return None

        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        if np.any(norms <= 1e-12):
            return None
        return matrix / norms

    def resolve_sections_with_vectors(
        self,
        sections: Dict[str, list[Any]],
        candidate_items: list[str],
        similarity_threshold: float = 0.65,
        embedder: Callable[[list[str]], Any] | None = None,
    ) -> tuple[Dict[str, list[Any]], Dict[str, list[dict[str, Any]]]]:
        """Replace extracted strings with their closest approved candidate.

        Numeric values remain unchanged. String values are replaced only when
        the maximum normalized dot-product score reaches the threshold.
        """
        if not -1.0 <= similarity_threshold <= 1.0:
            raise ValueError("similarity_threshold must be between -1.0 and 1.0")
        if not isinstance(candidate_items, list):
            raise TypeError("candidate_items must be a list[str]")

        candidates = list(
            dict.fromkeys(
                item.strip()
                for item in candidate_items
                if isinstance(item, str) and item.strip()
            )
        )
        resolved_sections = {
            section: list(values)
            for section, values in sections.items()
        }
        match_details: Dict[str, list[dict[str, Any]]] = {
            section: [] for section in sections
        }
        if not candidates:
            return resolved_sections, match_details

        query_items = list(
            dict.fromkeys(
                value
                for values in sections.values()
                for value in values
                if isinstance(value, str) and value
            )
        )
        if not query_items:
            return resolved_sections, match_details

        if embedder is None:
            from firegraph.embedder import embed_batch

            embedder = embed_batch

        query_matrix = self._normalized_matrix(embedder(query_items))
        candidate_matrix = self._normalized_matrix(embedder(candidates))
        if (
            query_matrix is None
            or candidate_matrix is None
            or query_matrix.shape[1] != candidate_matrix.shape[1]
        ):
            return resolved_sections, match_details

        similarity_matrix = np.dot(query_matrix, candidate_matrix.T)
        best_candidate_indices = np.argmax(similarity_matrix, axis=1)
        matches_by_item: dict[str, tuple[str, float]] = {}
        for query_index, original in enumerate(query_items):
            candidate_index = int(best_candidate_indices[query_index])
            matches_by_item[original] = (
                candidates[candidate_index],
                float(similarity_matrix[query_index, candidate_index]),
            )

        for section, values in sections.items():
            resolved_values = []
            for value in values:
                if not isinstance(value, str) or value not in matches_by_item:
                    resolved_values.append(value)
                    continue

                matched_item, score = matches_by_item[value]
                replaced = score >= similarity_threshold
                resolved_values.append(matched_item if replaced else value)
                match_details[section].append(
                    {
                        "original": value,
                        "matched_item": matched_item,
                        "compart_idx": candidate_items.index(matched_item),
                        "similarity": score,
                        "replaced": replaced,
                    }
                )
            resolved_sections[section] = resolved_values

        return resolved_sections, match_details

    def extract(
        self,
        text: str,
        candidate_items: list[str] | None = None,
        similarity_threshold: float = 0.65,
    ) -> Dict[str, Any]:
        """Extracts items and maps them to recognized section compartments (header, main, footer, plugins)."""
        sections: Dict[str, Any] = {sec: [] for sec in self.TARGET_SECTIONS}

        # Split prompt into clause segments (by commas, 'and', 'for', etc.)
        conjunction = "und" if self.language == "de" else "and"
        clauses = re.split(rf",|\b{conjunction}\b", text, flags=re.IGNORECASE)

        buffered_values: list[Any] = []
        active_prefix_section: str | None = None

        for clause in clauses:
            clause_tokens = self._tokenize(clause)
            if not clause_tokens:
                continue

            matched_section = None
            section_index = None

            # Find target section in the current clause
            for index, token in enumerate(clause_tokens):
                sec = self._match_section_name(token)
                if sec:
                    matched_section = sec
                    section_index = index
                    break

            if not matched_section:
                values = self._parse_tokens(clause_tokens)
                if active_prefix_section:
                    sections[active_prefix_section].extend(values)
                else:
                    buffered_values.extend(values)
                continue

            before_section = self._parse_tokens(clause_tokens[:section_index])
            after_section = self._parse_tokens(clause_tokens[section_index + 1:])

            if buffered_values or before_section:
                # Postfix form: "a, b, c for main".
                sections[matched_section].extend(buffered_values)
                sections[matched_section].extend(before_section)
                sections[matched_section].extend(after_section)
                buffered_values = []
                active_prefix_section = None
            else:
                # Prefix form: "main: a, b, c".
                active_prefix_section = matched_section
                sections[matched_section].extend(after_section)

        # Filter out empty sections dynamically
        final_sections = {k: v for k, v in sections.items() if v}

        result = {
            "sections": final_sections,
            "raw_input": text
        }
        if candidate_items is not None:
            resolved_sections, vector_matches = self.resolve_sections_with_vectors(
                final_sections,
                candidate_items,
                similarity_threshold=similarity_threshold,
            )
            result["resolved_sections"] = resolved_sections
            result["vector_matches"] = vector_matches
        return result


if __name__ == "__main__":
    extractor = QuerySectionCompartmentExtractor(language="en")
    prompt = "use egg in main, as of hello, abc and numer1. use abc, def, ghi, jkl, for heaeder and abrakadabra for footr and nothing for plugins"

    print(f"Input: '{prompt}'\n")
    res = extractor.extract(
        prompt,
        candidate_items=[
            (item[:-1] if item.endswith("/") else item).split("/")[-1]
            for item in MODEL_PATH_REGISTRY.keys()
        ]
    )
    print("Extracted Sections:")
    for section, content in res["sections"].items():
        print(f"  [{section}]: {content}")

    for section, content in res["resolved_sections"].items():
        print(f"  [{section}]: {content}")

    print("VECTOR MATCHES:")
    for section, content in res["vector_matches"].items():
        print(f"  [{section}]: {content}")
