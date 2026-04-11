"""quiz_gen.storage — persistent project and data management."""

from .projects import (
    QUIZ_GEN_HOME,
    DEFAULT_PROJECT,
    list_projects,
    create_project,
    delete_project,
    get_project_root,
    save_document,
    save_quiz,
    save_debug,
    list_project_documents,
    get_project_document,
    list_project_quizzes,
    get_project_quiz,
    router,
)

__all__ = [
    "QUIZ_GEN_HOME",
    "DEFAULT_PROJECT",
    "list_projects",
    "create_project",
    "delete_project",
    "get_project_root",
    "save_document",
    "save_quiz",
    "save_debug",
    "list_project_documents",
    "get_project_document",
    "list_project_quizzes",
    "get_project_quiz",
    "router",
]
