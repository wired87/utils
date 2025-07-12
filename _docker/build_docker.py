import docker


def build_docker(path: str, image_name: str, tag: str = "latest"):
    """
    Prüft, ob ein Docker-Image existiert. Wenn nicht, wird es gebaut.

    Args:
        path (str): Lokaler Pfad zum Docker-Kontext (enthält Dockerfile)
        image_name (str): Name des Docker-Images
        tag (str): Tag (default: "latest")
    """
    client = docker.from_env()

    # Check if image exists
    images = client.images.list(name=image_name)
    for img in images:
        if f"{image_name}:{tag}" in img.tags:
            print(f"✅ Image '{image_name}:{tag}' exists.")
            return

    print(f"🔨 Baue Image: {image_name}:{tag}")
    try:
        image, logs = client.images.build(path=path, tag=f"{image_name}:{tag}")
        for line in logs:
            if 'stream' in line:
                print(line['stream'].strip())
        print(f"✅ Build erfolgreich: {image_name}:{tag}")
    except Exception as e:
        print(f"❌ Fehler beim Build: {e}")

# Beispiel:
# build_docker_if_needed("./my_app", "my-image", "v1")
