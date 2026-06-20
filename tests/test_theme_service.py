import os
import shutil
import tempfile
import unittest

import yaml

from app.theme_service import ThemeService


class TestThemeService(unittest.TestCase):
    def setUp(self):
        self.themes_dir = tempfile.mkdtemp()
        self._write('animals.txt', ['lion', 'tiger', 'bear'])
        self._write('cities.txt', ['paris', 'tokyo'])
        with open(os.path.join(self.themes_dir, 'themes.yaml'), 'w') as f:
            yaml.safe_dump({'themes': [
                {'id': 'animal-city', 'name': 'Animal City',
                 'categories': ['animals', 'cities']},
                {'id': 'broken', 'name': 'Broken',
                 'categories': ['animals', 'missing']},
            ]}, f)
        self.service = ThemeService(themes_dir=self.themes_dir)

    def tearDown(self):
        shutil.rmtree(self.themes_dir)

    def _write(self, name, words):
        with open(os.path.join(self.themes_dir, name), 'w') as f:
            f.write('\n'.join(words) + '\n')

    def test_get_themes_skips_presets_with_missing_category(self):
        themes = self.service.get_themes()
        ids = [t['id'] for t in themes]
        self.assertEqual(ids, ['animal-city'])
        self.assertEqual(themes[0]['name'], 'Animal City')

    def test_generate_returns_count_combinations(self):
        combos = self.service.generate('animal-city', count=3)
        self.assertEqual(len(combos), 3)
        for combo in combos:
            animal, city = combo.split('-')
            self.assertIn(animal, ['lion', 'tiger', 'bear'])
            self.assertIn(city, ['paris', 'tokyo'])

    def test_generate_unknown_theme_raises(self):
        with self.assertRaises(ValueError):
            self.service.generate('nope')


if __name__ == '__main__':
    unittest.main()
