from text_to_num import text2num


def parse_number(num_str: str, lang: str = "de") -> int:
    """Konvertiert Strings ("10", "zehn", "ten") zuverlässig in ein Integer."""
    num_str = num_str.strip()

    try:
        # 1. Schnelle Direkt-Konvertierung für reine Ziffern ("10")
        return int(num_str)
    except ValueError:
        # 2. Text-zu-Zahl-Konvertierung ("zehn" -> 10, "ten" -> 10)
        return text2num(num_str, lang=lang)


# --- EXAMPLES ---
if __name__ == "__main__":
    print(parse_number("10"))  # 10
    print(parse_number("zehn", "de"))  # 10
    print(parse_number("ten", "en"))  # 10
    print(parse_number("thirtythree", "de"))  # 53