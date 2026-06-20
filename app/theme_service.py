import logging
import os
import random

import yaml


class ThemeService:
    """In-memory provider of themed word combinations.

    Reads named presets from ``<themes_dir>/themes.yaml`` and the curated word
    lists they reference (``<themes_dir>/<category>.txt``). The data is small, so
    everything is loaded into memory once at startup.
    """

    def __init__(self, themes_dir='themes'):
        self.themes_dir = themes_dir
        self.categories = {}   # category name -> [words]
        self.themes = []       # [{id, name, categories}]
        self._load()

    def _load(self):
        config_path = os.path.join(self.themes_dir, 'themes.yaml')
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f) or {}
        except OSError as e:
            logging.warning(f"Could not load themes config {config_path}: {e}")
            return

        for preset in config.get('themes', []):
            preset_id = preset.get('id')
            categories = preset.get('categories', [])
            if not preset_id or not categories:
                logging.warning(f"Skipping malformed theme preset: {preset!r}")
                continue

            # Lazily load each referenced category; skip the preset if any of its
            # categories is missing or empty so a typo can't 500 the endpoint.
            ok = True
            for category in categories:
                if category not in self.categories:
                    self.categories[category] = self._load_category(category)
                if not self.categories[category]:
                    logging.warning(
                        f"Theme '{preset_id}' references empty/missing category "
                        f"'{category}'; skipping preset."
                    )
                    ok = False
            if not ok:
                continue

            self.themes.append({
                'id': preset_id,
                'name': preset.get('name', preset_id),
                'categories': categories,
            })

    def _load_category(self, category):
        path = os.path.join(self.themes_dir, f'{category}.txt')
        try:
            with open(path, 'r') as f:
                return [line.strip() for line in f if line.strip()]
        except OSError as e:
            logging.warning(f"Could not load category file {path}: {e}")
            return []

    def get_themes(self):
        """Return the list of available presets for the UI dropdown."""
        return self.themes

    def generate(self, theme_id, count=1):
        """Return ``count`` combination strings for the given preset.

        Each combination picks one random word per category, joined with '-'.
        Raises ValueError for an unknown theme.
        """
        preset = next((t for t in self.themes if t['id'] == theme_id), None)
        if preset is None:
            raise ValueError(f"Unknown theme: {theme_id}")

        combinations = []
        for _ in range(count):
            words = [random.choice(self.categories[c]) for c in preset['categories']]
            combinations.append('-'.join(words))
        return combinations
