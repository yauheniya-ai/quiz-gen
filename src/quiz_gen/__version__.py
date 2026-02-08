"""Version information for quiz-gen package."""


try:
	from importlib.metadata import version
	__version__ = version("quiz-gen")
except Exception:
	# Fallback for local source runs (not installed as package)
	__version__ = "0.2.8"
