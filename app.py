from flask import Flask, request, abort
from flask_pymongo import PyMongo
from functools import wraps
from bson import json_util

app = Flask(__name__)

app.config['MONGO_DBNAME'] = 'heroku_k0kdm9jl'
app.config['MONGO_URI'] = 'mongodb://test_user:test_pass@ds157380.mlab.com:57380/heroku_k0kdm9jl'
app.secret_key = 'mysecret'

mongo = PyMongo(app)


def require_appkey(view_function):
    @wraps(view_function)
    def decorated_function(*args, **kwargs):
        if request.args.get('key') and key_exists(request.args.get('key')):
            return view_function(*args, **kwargs)
        else:
            abort(401)

    return decorated_function


@app.route('/')
@require_appkey
def root():
    return 'hello there'


@app.route('/questions', methods=['POST', 'GET'], defaults={'course': None, 'assignment': None, 'question': None})
@app.route('/questions/<course>/<assignment>/<question>', methods=['PUT', 'DELETE'])
@require_appkey
def questions(course, assignment, question):
    mongo_questions = mongo.db.questions
    teacheruser = user_name(request.args.get('key'))

    # get all questions for an assignment
    if request.method == 'GET':
        questions_resp = mongo_questions.find({'assignment_num': request.args.get('assignment_num'),
                                               'course_num': request.args.get('course_num'),
                                               'teacheruser': teacheruser})
        return json_util.dumps(questions_resp)

    # insert new question into assignment
    if request.method == 'POST':
        existing_question = mongo_questions.find_one({'number': request.args.get('number'),
                                                     'assignment_num': request.args.get('assignment_num'),
                                                     'course_num': request.args.get('course_num'),
                                                     'teacheruser': teacheruser})
        if existing_question is None:
            mongo_questions.insert({'number': request.args.get('number'),
                                    'assignment_num': request.args.get('assignment_num'),
                                    'course_num': request.args.get('course_num'),
                                    'question': request.args.get('question'),
                                    'question_type': request.args.get('question_type'),
                                    'options': request.args.get('options'),
                                    'answer': request.args.get('answer'),
                                    'teacheruser': teacheruser})
            return 'Added'

        return 'already exists!'

    # update a question
    if request.method == 'PUT':
        existing_question = mongo_questions.find_one({'number': question,
                                                      'assignment_num': assignment,
                                                      'course_num': course,
                                                      'teacheruser': teacheruser})
        if existing_question is not None:
            print(request.args)
            mongo_questions.update_one({'number': question,
                                        'assignment_num': assignment,
                                        'course_num': course,
                                        'teacheruser': teacheruser},
                                       {'$set': {'question': request.args.get('question'),
                                                 'question_type': request.args.get('question_type'),
                                                 'options': request.args.get('options'),
                                                 'answer': request.args.get('answer')}})

            return 'Updated'

        return 'Update failed'

    # delete a question
    if request.method == 'DELETE':
        existing_question = mongo_questions.find_one({'number': question,
                                                      'assignment_num': assignment,
                                                      'course_num': course,
                                                      'teacheruser': teacheruser})
        if existing_question is not None:
            mongo_questions.delete_one({'number': question,
                                        'assignment_num': assignment,
                                        'course_num': course,
                                        'teacheruser': teacheruser})
            return 'Deleted'

        return 'Delete failed'


def obj_dict(obj):
    return obj.__dict__


def user_name(key):
    users = mongo.db.users
    user = users.find_one({'apikey': key})
    return user['name']


def key_exists(key):
    users = mongo.db.users
    user_key = users.find_one({'apikey':key})

    if user_key is None:
        return False

    return True


if __name__ == '__main__':
    app.run(debug=True)
