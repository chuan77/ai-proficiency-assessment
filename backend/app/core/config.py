"""Application configuration loaded from environment variables."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """Runtime settings; every field can be overridden by an environment variable."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    lm_studio_url: str = "http://localhost:1234/v1"
    lm_studio_model: str = "gemma-4-26b-a4b-it-qat-mlx"
    llm_timeout_seconds: float = 180.0
    llm_temperature: float = 0.2
    questions_per_session: int = 10
    code_partial_credit: bool = False
    code_timeout_seconds: int = 3
    adaptive_min_questions: int = 8
    adaptive_max_questions: int = 15
    adaptive_start_difficulty: str = "intermediate"
    adaptive_performance_window: int = 2
    adaptive_topic_balancing: bool = True
    adaptive_correct_threshold: float = 0.6
    database_url: str = "sqlite:///./assessment.db"
    questions_path: Path = PROJECT_ROOT / "data" / "questions.json"
    prompts_dir: Path = PROJECT_ROOT / "prompts"


settings = Settings()
