from flask import Flask, render_template, request, url_for, redirect, session
import data_manager as dm
import util

app = Flask(__name__, template_folder='templates')
app.secret_key = 'ff'


@app.route('/')
def index():
    latest_questions = dm.get_latest_questions(5)
    return render_template('index.html', latest_questions=latest_questions, session=session)


@app.route("/list", methods=['GET'])
def list_questions():
    order_by = request.args.get('order_by', 'submission_time')
    order_direction = request.args.get('order_direction', 'desc')
    questions = dm.display_questions()  # ?
    sorted_questions = dm.sort_questions(order_by, order_direction)  # ?
    sorted_questions = dm.sort_questions(order_by, order_direction)
    return render_template('list.html',
                           questions=sorted_questions,
                           order_by=order_by,
                           order_direction=order_direction)


@app.route('/question/<int:question_id>')
def display_question(question_id):
    dm.update_question_views(question_id)
    question = dm.get_question_by_id(question_id)
    comments_to_question = dm.get_comments_for_question(question_id)
    answers = dm.get_answers_for_question(question_id)
    comments_to_answers = dm.get_comments_for_answers(question_id)
    tags = dm.get_question_tags(question_id)
    return render_template('question.html',
                           question=question,
                           comments_to_question=comments_to_question,
                           answers=answers,
                           comments_to_answers=comments_to_answers,
                           question_id=question_id,
                           tags=tags)


@app.route('/image/<int:question_id>')
def display_image(question_id):
    link = dm.get_image_link_by_question_id(question_id)
    return render_template('image.html', link=link)


@app.route('/add_question', methods=['GET', 'POST'])
def add_question():
    if request.method == 'GET':
        return render_template('add_question.html')
    elif request.method == 'POST':
        file = request.files['image']
        if file.filename != '':
            file.save(f'static/images/{file.filename}')
        title = request.form.get('title')
        message = request.form.get('message')
        image = file.filename
        new_question_id = dm.add_question(title, message, image=image)
        return redirect(url_for('display_question', question_id=new_question_id))


@app.route("/question/<int:question_id>/new-answer", methods=['GET', 'POST'])
def add_answer(question_id):
    if request.method == 'GET':
        return render_template('new_answer.html', question_id=question_id)
    elif request.method == 'POST':
        message = request.form.get('message')
        dm.add_answer(question_id, message)
        return redirect(url_for('display_question', question_id=question_id))


@app.route("/question/<question_id>/delete", methods=["POST"])
def delete_question(question_id):
    dm.delete_question(question_id)
    return redirect(url_for('list_questions'))


@app.route('/question/<int:question_id>/edit', methods=['GET', 'POST'])
def edit_question(question_id):
    if request.method == 'GET':
        question = dm.get_question_by_id(question_id)
        question_length = len(question['title'])
        return render_template('edit_question.html',
                               question=question,
                               question_length=question_length)
    elif request.method == 'POST':
        title = request.form.get('title')
        message = request.form.get('message')
        dm.edit_question(question_id, title, message)
        return redirect(url_for('display_question', question_id=question_id))


@app.route('/answer/<int:answer_id>/delete', methods=['POST'])
def delete_answer(answer_id):
    question_id = dm.delete_answer(answer_id)
    if question_id is not None:
        return redirect(url_for('display_question', question_id=question_id))
    else:
        return "Error: Question ID not found"


@app.route('/question/<int:question_id>/vote-up', methods=['POST'])
def vote_up(question_id):
    dm.vote_question(question_id, 'up')
    return redirect(url_for('list_questions'))


@app.route('/question/<int:question_id>/vote-down', methods=['POST'])
def vote_down(question_id):
    dm.vote_question(question_id, 'down')
    return redirect(url_for('list_questions'))


@app.route('/search_results')
def search_results():
    search_phrase = request.args.get('q')
    if len(search_phrase) > 0:
        results = dm.search_results(search_phrase)  # Wywołanie funkcji wyszukującej
        results = util.underline_phrase(results, search_phrase)
    else:
        results = 'No results'
    return render_template('search_results.html', search_phrase=search_phrase, results=results)


@app.route('/answer/<answer_id>/edit', methods=['GET', 'POST'])
def edit_answer(answer_id):
    if request.method == 'GET':
        answer = dm.get_answer_by_id(answer_id)
        return render_template('edit_answer.html', answer=answer)
    elif request.method == 'POST':
        message = request.form.get('message')
        dm.edit_answer(answer_id, message)
        question_id = dm.get_question_id_by_answer(answer_id)
        return redirect(url_for('display_question', question_id=question_id['question_id']))


@app.route('/question/<question_id>/new-tag', methods=['GET', 'POST'])
def add_tag(question_id):
    if request.method == 'GET':
        current_tags = dm.get_existing_tags()
        return render_template('add_tag.html', question_id=question_id, current_tags=current_tags)
    elif request.method == 'POST':
        tag_id = request.form.get('tag')
        if tag_id == "add_new_tag":
            new_tag = request.form.get('new_tag')
            tag_id = dm.add_new_tag(new_tag)
            dm.add_tag(tag_id, question_id)
        elif tag_id is not None:
            dm.add_tag(tag_id, question_id)
        return redirect(url_for('display_question', question_id=question_id))


@app.route("/answer/<int:answer_id>/new-comment", methods=['GET', 'POST'])
def add_comment_to_answer(answer_id):
    if request.method == 'GET':
        return render_template('add_comment_to_answer.html', answer_id=answer_id)
    else:
        message = request.form.get('comment')
        question_id = dm.add_comment_to_answer(answer_id, message)
        return redirect(url_for('display_question', question_id=question_id))


@app.route("/question/<int:question_id>/new-comment", methods=['GET', 'POST'])
def add_comment_to_question(question_id):
    if request.method == 'GET':
        return render_template('add_comment_to_question.html', question_id=question_id)
    else:
        comment = request.form.get('comment')
        dm.add_comment_to_question(question_id, comment)
        return redirect(url_for('display_question', question_id=question_id))


@app.route("/question/<question_id>/tag/<tag_id>/delete")
def delete_tag(question_id, tag_id):
    dm.delete_tag_from_question(question_id, tag_id)
    return redirect(url_for('display_question', question_id=question_id))


@app.route("/comment/<comment_id>/edit", methods=['GET', 'POST'])
def edit_comment(comment_id):
    if request.method == 'GET':
        comment = dm.get_comment_by_id(comment_id)
        return render_template('edit_comment.html', comment=comment)
    elif request.method == 'POST':
        message = request.form.get('message')
        dm.edit_comment(comment_id, message)
        question_id = dm.get_question_id_by_comment(comment_id)
        return redirect(url_for('display_question', question_id=question_id))


@app.route('/comments/<int:comment_id>/delete', methods=["POST"])
def delete_comment(comment_id):
    question_id = dm.delete_comment(comment_id)
    if question_id is not None:
        return redirect(url_for('display_question', question_id=question_id))
    else:
        answer_id = dm.delete_comment(comment_id)
        if answer_id is not None:
            question_id = dm.get_question_id_by_answer_id(answer_id)
            return redirect(url_for('display_question', question_id=question_id))
        else:
            return "Error: Comment ID not found"


@app.route('/registration', methods=["GET", "POST"])
def registration():
    if request.method == 'GET':
        return render_template('registration.html')
    elif request.method == 'POST':
        email = request.form.get("email")
        password = request.form.get("password")
        user_id = dm.register_user(email, password)
        session["user"] = user_id   # otwarcie sesji
        return redirect(url_for('index'))


@app.route('/logout')
def logout():
    session.pop("user")
    return redirect('/')


if __name__ == "__main__":
    app.run(debug=True)
