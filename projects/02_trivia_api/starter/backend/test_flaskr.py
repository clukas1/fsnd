import os
import unittest
import json
from flask_sqlalchemy import SQLAlchemy

from flaskr import create_app
from models import setup_db, Question, Category


class TriviaTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app()
        self.client = self.app.test_client
        self.database_name = "trivia_test"
        self.database_path = "postgres://{}/{}".format('localhost:5432', self.database_name)
        setup_db(self.app, self.database_path)

        # binds the app to the current context
        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)
            # create all tables
            self.db.create_all()

    def tearDown(self):
        """Executed after reach test"""
        pass

    """
    TODO
    Write at least one test for each test for successful operation and for expected errors.
    """
    def test_get_categories(self):
        res = self.client().get('/categories')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['total_categories'])
        self.assertTrue(len(data['categories']))

    def test_405_sent_post_get_categories_request(self):
        res = self.client().post('/categories')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 405)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'method not allowed')

    def test_get_paginated_questions(self):
        res = self.client().get('/questions')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['total_questions'])
        self.assertTrue(len(data['questions']))
        self.assertTrue(len(data['categories']))
        self.assertIsNone(data['current_category'])
        self.assertEqual(data['current_page'], 1)

    def test_404_sent_requesting_beyond_valid_page(self):
        res = self.client().get('/questions?page=1000', json={'rating':1})
        self.do_tests_for_404(res)

    def test_delete_question(self):
        questionId = 12
        res = self.client().delete('questions/{}'.format(questionId))
        data = json.loads(res.data)

        question = Question.query.filter(Question.id == questionId).one_or_none()

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertEqual(data['deleted'], questionId)
        self.assertEqual(data['total_questions'], Question.query.count())

    def test_invalid_id_delete_question(self):
        questionId = 1200
        res = self.client().delete('questions/{}'.format(questionId))
        self.do_tests_for_404(res)

    def test_create_question(self):

        newQuestion = {
            'question': 'How do you do?',
            'answer': 'marvelous',
            'category': 5,
            'difficulty': 1
        }

        res = self.client().post('/questions', json=newQuestion)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(len(data['question']))
        self.assertEqual(data['total_questions'], Question.query.count())

    def test_missing_data_create_question(self):

        newQuestion = {
            'question': 'How do you do?',
            'answer': 'marvelous',
            'category': 5,
        }

        res = self.client().post('/questions', json=newQuestion)
        self.do_tests_for_400(res)

    def test_search_question(self):

        data = {
            'searchTerm': 'did',
        }
        expectedNumSearchResults = 2

        res = self.client().post('/questions', json=data)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertEqual(len(data['questions']), expectedNumSearchResults)
        self.assertEqual(data['total_questions'], expectedNumSearchResults)
        self.assertTrue(len(data['categories']))
        self.assertEqual(data['current_page'], 1)

    def test_search_question_with_page(self):

        data = {
            'searchTerm': 'a',
            'page': 2,
        }

        res = self.client().post('/questions', json=data)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertEqual(len(data['questions']), 6)
        self.assertEqual(data['total_questions'], 16)
        self.assertTrue(len(data['categories']))
        self.assertEqual(data['current_page'], 2)

    def test_search_with_no_results(self):
        data = {
            'searchTerm': 'xyz',
        }

        res = self.client().post('/questions', json=data)
        self.do_tests_for_422(res)

    def test_get_questions_for_category(self):
        queriedCategoryId = 3
        res = self.client().get('/categories/{}/questions'.format(queriedCategoryId))
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['total_questions'])
        self.assertTrue(len(data['questions']))
        self.assertTrue(len(data['categories']))
        self.assertEqual(data['current_category'], queriedCategoryId)

    def test_get_questions_for_invalid_category(self):
        queriedCategoryId = 1000
        res = self.client().get('/categories/{}/questions'.format(queriedCategoryId))
        self.do_tests_for_404(res)

    def test_get_next_quiz_question(self):
        data = {
            'quiz_category': {'type':'Science', 'id':1},
            'previous_questions': [0],
        }
        res = self.client().post('/quizzes', json=data)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(len(data['question']))

    def test_get_next_quiz_question_for_invalid_category(self):
        data = {
            'quiz_category': {'type':'Random Stuff', 'id':100},
            'previous_questions': [0],
        }
        res = self.client().post('/quizzes', json=data)
        data = json.loads(res.data)
        self.do_tests_for_422(res)

    def do_tests_for_400(self, res):
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'bad request')

    def do_tests_for_404(self, res):
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'resource not found')

    def do_tests_for_422(self, res):
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 422)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'unprocessable')

# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()
