import tempfile


def save_temp(name, content):
    ftype=name.split('.')[-1]
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=f".{ftype}")
    temp.write(content)
    temp.flush()  # Ensure all content is written
    temp.seek(0)  # Optional: go back to beginning if needed
    temp_path = temp.name
    print("Temp path:", temp_path)
    return temp_path