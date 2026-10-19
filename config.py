"""Environment-backed application settings (no secrets in the frontend)."""
from dataclasses import dataclass
import os


def _csv(name: str, default: str) -> list[str]:
    return [part.strip() for part in os.getenv(name, default).split(",") if part.strip()]


@dataclass(frozen=True)
class Settings:
    database_path: str = os.getenv("DATABASE_PATH", "./routewise.db")
    cors_origins: tuple[str, ...] = tuple(_csv("CORS_ORIGINS", "http://localhost:5500,http://127.0.0.1:5500"))
    nominatim_url: str = os.getenv("NOMINATIM_URL", "https://nominatim.openstreetmap.org/search")
    nominatim_user_agent: str = os.getenv("NOMINATIM_USER_AGENT", "RouteWiseAI/1.0 (configure-contact@example.com)")
    nominatim_min_interval: float = float(os.getenv("NOMINATIM_MIN_INTERVAL", "1.1"))
    osrm_url: str = os.getenv("OSRM_URL", "https://router.project-osrm.org")
    cloudinary_cloud_name: str = os.getenv("CLOUDINARY_CLOUD_NAME", "")
    cloudinary_api_key: str = os.getenv("CLOUDINARY_API_KEY", "")
    cloudinary_api_secret: str = os.getenv("CLOUDINARY_API_SECRET", "")
    cloudinary_upload_preset: str = os.getenv("CLOUDINARY_UPLOAD_PRESET", "")
    cloudinary_folder: str = os.getenv("CLOUDINARY_FOLDER", "routewise/proof-of-delivery")
    max_upload_bytes: int = int(os.getenv("MAX_UPLOAD_BYTES", str(10 * 1024 * 1024)))


settings = Settings()
