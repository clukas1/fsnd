import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)
    CORS(app)

    '''
    @TODO: Set up CORS. Allow '*' for origins. Delete the sample
    route after completing the TODOs
    '''
    '''
    @TODO: Use the after_request decorator to set Access-Control-Allow
    '''
    # CORS Headers
    @app.after_request
    def after_request(response):
        response.headers.add(
            'Access-Control-Allow-Headers',
            'Content-Type,Authorization'
        )
        response.headers.add(
            'Access-Control-Allow-Methods',
            'GET,PUT,POST,DELETE,OPTIONS'
        )
        return response

    '''
    @TODO:
    Create an endpoint to handle GET requests
    for all available categories.
    '''
    @app.route('/categories', methods=['GET'])
    def get_categories():
        categories = Category.query.all()
        formatted_categories = {cat.id: cat.type for cat in categories}

        if len(formatted_categories) == 0:
            abort(404)

        return jsonify({
            'success': True,
            'categories': formatted_categories,
            'total_categories': len(formatted_categories)
        })

    '''
    @TODO:
    Create an endpoint to handle GET requests for questions,
    including pagination (every 10 questions).
    This endpoint should return a list of questions,
    number of total questions, current category, categories.

    TEST: At this point, when you start the application
    you should see questions and categories generated,
    ten questions per page and pagination at the bottom of
    the screen for three pages.
    Clicking on the page numbers should update the questions.
    '''
    @app.route('/questions', methods=['GET'])
    def get_questions():

        questions = Question.query.all()
        page = request.args.get('page', 1, type=int)
        formatted_questions = [question.format() for question in questions]
        paginated_qustions = paginate_questions(page, formatted_questions)

        if len(paginated_qustions) == 0:
            abort(404)

        return jsonify({
            'success': True,
            'questions': paginated_qustions,
            'total_questions': len(formatted_questions),
            'categories': get_formatted_categories(),
            'current_category': None,
            'current_page': page,
        })

    def paginate_questions(page, questions):
        start = (page-1) * QUESTIONS_PER_PAGE
        end = start + QUESTIONS_PER_PAGE

        current_questions = questions[start:end]
        return current_questions

    '''
    @TODO:
    Create an endpoint to DELETE question using a question ID.

    TEST: When you click the trash icon next to a question,
    the question will be removed.
    This removal will persist in the database and when you refresh the page.
    '''
    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):

        question = Question.query.get_or_404(question_id)
        question.delete()

        return jsonify({
            'success': True,
            'deleted': question_id,
            'total_questions': Question.query.count()
        })

    '''
    @TODO:
    Create an endpoint to POST a new question,
    which will require the question and answer text,
    category, and difficulty score.

    TEST: When you submit a question on the "Add" tab,
    the form will clear and the question will appear at
    the end of the last page of the questions list in
    the "List" tab.
    '''
    '''
    @TODO:
    Create a POST endpoint to get questions based on a search term.
    It should return any questions for whom the search term
    is a substring of the question.

    TEST: Search by any phrase. The questions list will update to include
    only question that include that string within their question.
    Try using the word "title" to start.
    '''

    @app.route('/questions', methods=['POST'])
    def create_or_search_question():

        body = request.get_json()

        searchTerm = body.get('searchTerm')
        if searchTerm:
            page = body.get('page')

            if not isinstance(page, int):
                page = 1

            try:
                questions = Question.query.filter(
                    Question.question.ilike('%{}%'.format(searchTerm))
                ).all()
                formatted_questions = [
                    question.format() for question in questions
                ]
                paginated_qustions = paginate_questions(
                    page,
                    formatted_questions
                )

                if len(formatted_questions) == 0:
                    abort(404)

                return jsonify({
                    'success': True,
                    'questions': paginated_qustions,
                    'total_questions': len(formatted_questions),
                    'categories': get_formatted_categories(),
                    'current_category': None,
                    'current_page': page
                })
            except Exception as e:
                print(e)
                abort(422)

        else:
            question = body.get('question')
            answer = body.get('answer')
            category = body.get('category')
            difficulty = body.get('difficulty')

            # actually would have liked to do this check within the model and
            # not null constraints in the db, but this would require a new
            # migration and a try/except block within insert(), hence I was
            # to lazy.
            if not question or not answer or not category or not difficulty:
                abort(400)

            try:
                question = Question(question, answer, category, difficulty)
                question.insert()

                return jsonify({
                    'success': True,
                    'question': question.format(),
                    'total_questions': Question.query.count()
                })
            except Exception as e:
                print(e)
                abort(400)

    '''
    @TODO:
    Create a GET endpoint to get questions based on category.

    TEST: In the "List" tab / main screen, clicking on one of the
    categories in the left column will cause only questions of that
    category to be shown.
    '''
    @app.route('/categories/<int:category_id>/questions', methods=['GET'])
    def show_category_questions(category_id):

        # check if categegory exists first if not return 404
        category = Category.query.get_or_404(category_id)

        try:
            # query and paginate questions
            questions = Question.query.filter(
                Question.category == category_id
            ).all()
            page = request.args.get('page', 1, type=int)
            formatted_questions = [question.format() for question in questions]
            paginated_qustions = paginate_questions(page, formatted_questions)

            return jsonify({
                'success': True,
                'questions': paginated_qustions,
                'total_questions': len(formatted_questions),
                'categories': get_formatted_categories(),
                'current_category': category_id,
            })
        except Exception as e:
            print(e)
            abort(400)
    '''
    @TODO:
    Create a POST endpoint to get questions to play the quiz.
    This endpoint should take category and previous question parameters
    and return a random questions within the given category,
    if provided, and that is not one of the previous questions.

    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not.
    '''
    @app.route('/quizzes', methods=['POST'])
    def show_next_quiz_question():

        body = request.get_json()
        previous_questions = body.get('previous_questions')
        quiz_category = body.get('quiz_category')

        if quiz_category['id'] != 0:
            # check if categegory exists first if not return 422
            category = Category.query.get(quiz_category['id'])
            if not category:
                abort(422)

            # then get questions
            questions = Question.query.filter(
                Question.category == quiz_category['id']
            ).all()
        else:
            questions = Question.query.all()

        if not questions:
            abort(422)

        random.shuffle(questions)

        if not previous_questions:
            previous_questions = []

        question = None
        index = 0

        while not question:
            try:
                if questions[index].id in previous_questions:
                    index += 1
                else:
                    question = questions[index]
            except Exception as e:
                print(e)
                abort(422)

        return jsonify({
            'success': True,
            'question': question.format(),
        })

    def get_formatted_categories():
        categories = Category.query.all()
        formatted_categories = {cat.id: cat.type for cat in categories}
        return formatted_categories

    '''
    @TODO:
    Create error handlers for all expected errors
    including 404 and 422.
    '''
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': 404,
            'message': 'resource not found',
        }), 404

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'success': False,
            'error': 400,
            'message': 'bad request',
        }), 400

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            'success': False,
            'error': 405,
            'message': 'method not allowed',
        }), 405

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            'success': False,
            'error': 422,
            'message': 'unprocessable',
        }), 422

    return app
