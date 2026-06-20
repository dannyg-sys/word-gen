import unittest
import json
import yaml
from app.webapp import app
from app.word_service import WordService
from app.theme_service import ThemeService
import tempfile
import os

class TestWebApp(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()

        # Set up a test database
        self.test_db = 'test_words.db'
        self.word_service = WordService(self.test_db)

        # Create and populate test words file
        self.temp_dir = tempfile.mkdtemp()
        self.words_file = os.path.join(self.temp_dir, 'test_words.txt')
        with open(self.words_file, 'w') as f:
            f.write('hello\nworld\ntest\n')

        # Initialize database with test words
        self.word_service.initialize_from_file(self.words_file)

        # Set up a themed-word service from a temp themes dir
        self.themes_dir = tempfile.mkdtemp()
        with open(os.path.join(self.themes_dir, 'animals.txt'), 'w') as f:
            f.write('lion\ntiger\n')
        with open(os.path.join(self.themes_dir, 'cities.txt'), 'w') as f:
            f.write('paris\ntokyo\n')
        with open(os.path.join(self.themes_dir, 'themes.yaml'), 'w') as f:
            yaml.safe_dump({'themes': [
                {'id': 'animal-city', 'name': 'Animal City',
                 'categories': ['animals', 'cities']},
            ]}, f)
        self.theme_service = ThemeService(themes_dir=self.themes_dir)

        # Set the services in the app
        import app.webapp as webapp
        webapp.init_word_service(self.word_service)
        webapp.init_theme_service(self.theme_service)

    def tearDown(self):
        self.word_service.close()
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
        if os.path.exists(self.words_file):
            os.remove(self.words_file)
        os.rmdir(self.temp_dir)
        import shutil
        shutil.rmtree(self.themes_dir)

    def test_get_words(self):
        response = self.client.post('/words',
                                  data=json.dumps({'wordLength': 5, 'numberOfWords': 1}),
                                  content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('words', data)
        self.assertTrue(isinstance(data['words'], str))

    def test_invalid_request(self):
        response = self.client.post('/words',
                                  data=json.dumps({'wordLength': -1, 'numberOfWords': 1}),
                                  content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_get_themes(self):
        response = self.client.get('/themes')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual([t['id'] for t in data['themes']], ['animal-city'])

    def test_themed_words(self):
        response = self.client.post('/themed',
                                  data=json.dumps({'theme': 'animal-city', 'count': 2}),
                                  content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        lines = data['words'].split('\n')
        self.assertEqual(len(lines), 2)
        for line in lines:
            animal, city = line.split('-')
            self.assertIn(animal, ['lion', 'tiger'])
            self.assertIn(city, ['paris', 'tokyo'])

    def test_themed_unknown_theme(self):
        response = self.client.post('/themed',
                                  data=json.dumps({'theme': 'bogus'}),
                                  content_type='application/json')
        self.assertEqual(response.status_code, 400)

if __name__ == '__main__':
    unittest.main() 