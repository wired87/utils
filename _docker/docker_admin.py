import docker
from pathlib import Path

from _ray_core.base.main import RayAdminBase
from build_docker import build_docker
from dockerfile import get_custom_dockerfile_content
from dynamic_docker import generate_dockerfile
from qf_core_base.qf_utils.all_subs import ALL_SUBS


class DockerAdmin:
    def __init__(self, context_path: str = ".", dockerfile_name: str = "Dockerfile"):
        self.context_path = Path(context_path)
        self.dockerfile_path = self.context_path / dockerfile_name
        self.client = docker.from_env()

    # --- Dockerfile-Erstellung ---
    def create_static_dockerfile(
        self,
        base_ray_image: str,
        requirements_file: str,
        app_script_name: str
    ):
        """Erstellt ein statisches Dockerfile aus Basis-Template."""
        content = get_custom_dockerfile_content(
            base_ray_image=base_ray_image,
            requirements_file=requirements_file,
            app_script_name=app_script_name
        )
        self._write_dockerfile(content)
        print(f"✅ Static Dockerfile erstellt: {self.dockerfile_path}")

    def create_dynamic_dockerfile(self, project_root, startup_cmd, **env_vars):
        """Erstellt ein dynamisches Dockerfile mit ENV-Variablen."""
        content = generate_dockerfile(
            project_root=project_root,
            startup_cmd=startup_cmd,
            **env_vars
        )
        print(f"✅ Dynamic Dockerfile erstellt: {self.dockerfile_path}")
        return content



    def _write_dockerfile(self, content: str):
        self.dockerfile_path.write_text(content)

    # --- Docker Image Build ---
    def build_image(self, image_name: str, tag: str = "latest"):
        """Baut ein Image, wenn es nicht bereits existiert."""
        build_docker(str(self.context_path), image_name, tag)

    def force_build_image(self, image_name: str, tag: str = "latest"):
        """Baut ein Image immer neu."""
        print(f"🔨 Force-Build: {image_name}:{tag}")
        try:
            image, logs = self.client.images.build(
                path=str(self.context_path),
                tag=f"{image_name}:{tag}"
            )
            for line in logs:
                if 'stream' in line:
                    print(line['stream'].strip())
            print(f"✅ Build erfolgreich: {image_name}:{tag}")
        except Exception as e:
            print(f"❌ Fehler beim Build: {e}")

    # --- Utility ---
    def image_exists(self, image_name: str, tag: str = "latest") -> bool:
        """Prüft, ob ein Image mit Tag existiert."""
        images = self.client.images.list(name=image_name)
        return any(f"{image_name}:{tag}" in img.tags for img in images)


# --- Beispielnutzung ---
if __name__ == "__main__":
    admin = DockerAdmin(".")
    ray_admin = RayAdminBase()

    # Statisches Dockerfile
    static_env_vars = ray_admin.create_static_docker_env_vars()
    for sub in ALL_SUBS:
        static_env_vars.update({"FIELD_TYPE": sub})
        content = admin.create_dynamic_dockerfile(
            roject_root=rf"C:\Users\wired\OneDrive\Desktop\Projects\qfs",
            startup_cmd="python main.py",
            **static_env_vars
        )


    # Build
    admin.build_image("my-image", "v1")
