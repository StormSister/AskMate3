import database_common as db
import util
import bcrypt


def get_questions_sorted_by_date(cursor):
    query = """
        SELECT * FROM question ORDER BY submission_time DESC
    """
    cursor.execute(query)
    return cursor.fetchall()


@db.connection_handler
def display_questions(cursor):
    return get_questions_sorted_by_date(cursor)


@db.connection_handler
def get_question_by_id(cursor, question_id):
    query = """
        SELECT * FROM question
        WHERE id = %(question_id)s;
    """
    cursor.execute(query, {'question_id': question_id})
    return cursor.fetchone()


@db.connection_handler
def get_answers_for_question(cursor, question_id):
    query = """
        SELECT * FROM answer
        WHERE question_id = %(question_id)s
        ORDER BY submission_time DESC;
    """
    cursor.execute(query, {'question_id': question_id})
    return cursor.fetchall()


@db.connection_handler
def add_question(cursor, title, message, image):
    current_timestamp = util.get_current_timestamp()
    image_path = f'images/{image}'
    new_question = {
        'submission_time': current_timestamp,
        'view_number': 0,
        'vote_number': 0,
        'title': title,
        'message': message,
        'image': image_path
    }
    query = """
            INSERT INTO question (submission_time, view_number, vote_number, title, message, image)
            VALUES (%(submission_time)s, %(view_number)s, %(vote_number)s, %(title)s, %(message)s, %(image)s);
            SELECT id FROM question
            WHERE message=%(message)s;
        """
    cursor.execute(query, new_question)
    return cursor.fetchone()['id']


@db.connection_handler
def add_answer(cursor, question_id, message):
    query = """
        INSERT INTO answer (submission_time, vote_number, question_id, message, image)
        VALUES (CURRENT_TIMESTAMP, 0, %(question_id)s, %(message)s, '');
    """
    cursor.execute(query, {'question_id': question_id, 'message': message})
    return cursor.lastrowid


@db.connection_handler
def delete_question(cursor, question_id):

    query_1 = """
        DELETE FROM question WHERE id = %(question_id)s
        """
    query_2 = """
            DELETE FROM answer WHERE question_id = %(question_id)s
        """
    query_3 = """
        DELETE FROM comment WHERE comment.question_id = %(question_id)s
        """
    query_4 = """
        DELETE FROM comment 
        USING answer WHERE comment.answer_id = answer.id
        AND answer.question_id = %(question_id)s;
        """
    query_5 = """
        DELETE FROM question_tag 
        WHERE question_id = %(question_id)s
        """
    cursor.execute(query_5, {'question_id': question_id})
    cursor.execute(query_4, {'question_id': question_id})
    cursor.execute(query_3, {'question_id': question_id})
    cursor.execute(query_2, {'question_id': question_id})
    cursor.execute(query_1, {'question_id': question_id})


@db.connection_handler
def delete_answer(cursor, answer_id):
    get_answer_id_query = """
        SELECT question_id FROM answer WHERE id = %(answer_id)s;
    """
    cursor.execute(get_answer_id_query, {'answer_id': answer_id})
    question_id = cursor.fetchone()['question_id']
    query_1 = """
        DELETE FROM answer 
        WHERE id = %(answer_id)s;
        """
    query_2 = """
        DELETE FROM comment WHERE answer_id = %(answer_id)s;
        """
    cursor.execute(query_2, {'answer_id': answer_id})
    cursor.execute(query_1, {'answer_id': answer_id})
    return question_id


@db.connection_handler
def delete_comment(cursor, comment_id):
    get_ids_query = """
        SELECT question_id, answer_id FROM comment WHERE id = %(comment_id)s;
    """
    cursor.execute(get_ids_query, {'comment_id': comment_id})
    result = cursor.fetchone()
    question_id = result['question_id']
    answer_id = result['answer_id']

    if question_id:
        delete_query = """
            DELETE FROM comment WHERE id = %(comment_id)s AND question_id = %(question_id)s;
        """
        cursor.execute(delete_query, {'comment_id': comment_id, 'question_id': question_id})
        return question_id
    elif answer_id:
        delete_query = """
            DELETE FROM comment WHERE id = %(comment_id)s AND answer_id = %(answer_id)s;
        """
        cursor.execute(delete_query, {'comment_id': comment_id, 'answer_id': answer_id})
        return answer_id
    else:
        return None


@db.connection_handler
def edit_question(cursor, question_id, title, message):
    query = """
        UPDATE question
        SET title = %(title)s, message = %(message)s
        WHERE id = %(question_id)s;
    """
    cursor.execute(query, {'title': title, 'message': message, 'question_id': question_id})


@db.connection_handler
def vote_question(cursor, question_id, vote_type):
    query_1 = "SELECT vote_number FROM question WHERE id=%(question_id)s"
    cursor.execute(query_1, {'question_id': question_id})
    vote_number = cursor.fetchone()['vote_number']
    if vote_type == 'up':
        query_2 = """
                UPDATE question
                SET vote_number = vote_number + %(vote)s
                WHERE id=%(question_id)s;
                """
        cursor.execute(query_2, {'question_id': question_id, 'vote': 1})
    elif vote_type == 'down' and vote_number > 0:
        query_2 = """
                UPDATE question
                SET vote_number = vote_number + %(vote)s
                WHERE id=%(question_id)s;
                """
        cursor.execute(query_2, {'question_id': question_id, 'vote': -1})


@db.connection_handler
def update_question_views(cursor, question_id):
    query = """UPDATE question 
        SET view_number = view_number + 1
        WHERE id=%s 
    """
    cursor.execute(query, (question_id,))


@db.connection_handler
def get_all_questions_ordered(cursor, order_by, order_direction):
    query = f"""
        SELECT * FROM question
        ORDER BY {order_by} {order_direction}
    """
    cursor.execute(query)
    return cursor.fetchall()


@db.connection_handler
def get_latest_questions(cursor, number):
    query = f"""
        SELECT * FROM question
        ORDER BY submission_time DESC
        LIMIT %(number)s
    """
    cursor.execute(query, {'number': number})
    return cursor.fetchall()


@db.connection_handler
def get_image_link_by_question_id(cursor, question_id):
    query = """
        SELECT image FROM question
        WHERE id=%s;
    """
    cursor.execute(query, (question_id,))
    return cursor.fetchone()


@db.connection_handler
def search_results(cursor, search_phrase):
    query = f"""
        SELECT DISTINCT question.* FROM question
        LEFT JOIN answer ON question.id = answer.question_id
        WHERE question.title ILIKE '%%{search_phrase}%%'
        OR question.message ILIKE '%%{search_phrase}%%'
        OR answer.message ILIKE '%%{search_phrase}%%'
    """
    cursor.execute(query)
    return cursor.fetchall()


@db.connection_handler
def get_answer_by_id(cursor, answer_id):
    query = """
        SELECT * FROM answer
        WHERE id = %(answer_id)s;
    """
    cursor.execute(query, {'answer_id': answer_id})
    return cursor.fetchone()


@db.connection_handler
def edit_answer(cursor, answer_id, message):
    submission_time = util.get_current_timestamp()
    query = """
        UPDATE answer
        SET message = %(message)s, submission_time = %(submission_time)s
        WHERE id = %(answer_id)s;
    """
    cursor.execute(query, {'message': message, 'answer_id': answer_id, 'submission_time': submission_time})


@db.connection_handler
def get_question_id_by_answer(cursor, answer_id):
    query = """
            SELECT question_id FROM answer
            WHERE id = %(answer_id)s;
    """
    cursor.execute(query, {'answer_id': answer_id})
    return cursor.fetchone()


@db.connection_handler
def get_question_tags(cursor, question_id):
    query = """
            SELECT question_id, tag_id, name
            FROM question_tag
            LEFT JOIN tag
            ON question_tag.tag_id = tag.id
            WHERE question_id = %(question_id)s;
    """
    cursor.execute(query, {'question_id': question_id})
    return cursor.fetchall()


@db.connection_handler
def get_question_id_by_answer_id(cursor, answer_id):
    query = """
        SELECT question_id FROM answer WHERE id = %(answer_id)s;
    """
    cursor.execute(query, {'answer_id': answer_id})
    result = cursor.fetchone()
    if result:
        return result['question_id']
    else:
        return None


@db.connection_handler
def get_existing_tags(cursor):
    query = """
            SELECT * FROM tag
            ORDER BY id;
    """
    cursor.execute(query)
    return cursor.fetchall()


@db.connection_handler
def check_for_tag(cursor, tag_name):
    query = """
            SELECT CASE WHEN EXISTS (SELECT * FROM tag
                         WHERE name = %(tag_name)s)
            THEN (SELECT id FROM tag
                  WHERE name = %(tag_name)s)
            ELSE CAST (0 AS INTEGER) END;
    """
    cursor.execute(query, {'tag_name': tag_name})
    tag_result = cursor.fetchone()
    return tag_result['case']


@db.connection_handler
def is_tag_already_added(cursor, tag_id, question_id):
    query = """
            SELECT CASE WHEN EXISTS (SELECT * FROM question_tag
                WHERE tag_id = %(tag_id)s AND question_id = %(question_id)s)
            THEN CAST (1 AS INTEGER)
            ELSE CAST (0 AS INTEGER) END;
        """
    cursor.execute(query, {'question_id': question_id, 'tag_id': tag_id})
    result = cursor.fetchone()
    return result['case']


@db.connection_handler
def add_tag(cursor, tag_id, question_id):
    if is_tag_already_added(tag_id, question_id) == 1:
        return
    query = """
            INSERT INTO question_tag (question_id, tag_id)
            VALUES (%(question_id)s, %(tag_id)s);
    """
    cursor.execute(query, {'question_id': question_id, 'tag_id': tag_id})


@db.connection_handler
def add_new_tag(cursor, tag_name):
    tag_id = check_for_tag(tag_name)
    if tag_id != 0:
        return tag_id

    query = """
            INSERT INTO tag (name)
            VALUES (%(name)s);
    """
    cursor.execute(query, {'name': tag_name})

    query = """
            SELECT id FROM tag
            WHERE name = %(name)s;
       """
    cursor.execute(query, {'name': tag_name})
    tag_id = cursor.fetchone()
    return tag_id['id']


@db.connection_handler
def add_comment_to_answer(cursor, answer_id, message):
    submission_time = util.get_current_timestamp()
    query_1 = """
        INSERT INTO comment (answer_id, message, submission_time)
        VALUES (%(answer_id)s, %(message)s, %(submission_time)s)
        """
    cursor.execute(query_1, {'answer_id': answer_id, 'message': message, 'submission_time': submission_time})
    query_2 = """
        SELECT question_id FROM answer
        WHERE id=%(answer_id)s;
    """
    cursor.execute(query_2, {'answer_id': answer_id})
    return cursor.fetchone()['question_id']


@db.connection_handler
def get_comments_for_question(cursor, question_id):
    query = """
        SELECT * FROM comment
        WHERE question_id=%s
        ORDER BY submission_time DESC;
    """
    cursor.execute(query, (question_id,))
    return cursor.fetchall()


@db.connection_handler
def get_comments_for_answers(cursor, question_id):
    query_1 = """
        SELECT id FROM answer
        WHERE question_id=%s
    """
    cursor.execute(query_1, (question_id,))
    id_list = tuple([x['id'] for x in cursor.fetchall()])
    if len(id_list) == 0:
        return None
    else:
        query_2 = """
            SELECT * FROM comment
            WHERE answer_id IN %(id_list)s
            ORDER BY submission_time DESC;
        """
        cursor.execute(query_2, {'id_list': id_list})
        return cursor.fetchall()


@db.connection_handler
def add_comment_to_question(cursor, question_id, message):
    submission_time = util.get_current_timestamp()
    query = """
    INSERT INTO comment (question_id, message, submission_time)
    VALUES (%(question_id)s, %(message)s, %(submission_time)s)
    """
    cursor.execute(query, {'question_id': question_id,
                           'message': message,
                           'submission_time': submission_time})
    return question_id


@db.connection_handler
def sort_questions(cursor, order_by, order_direction):
    cursor.execute("SELECT * FROM question ORDER BY {} {}".format(order_by, order_direction))
    return cursor.fetchall()


@db.connection_handler
def delete_tag_from_question(cursor, question_id, tag_id):
    query = """
            DELETE FROM question_tag
            WHERE question_id = %(question_id)s AND tag_id = %(tag_id)s
    """
    cursor.execute(query, {'question_id': question_id, 'tag_id': tag_id})


@db.connection_handler
def get_comment_by_id(cursor, comment_id):
    query = """
            SELECT * FROM comment
            WHERE id = %(comment_id)s
    """
    cursor.execute(query, {'comment_id': comment_id})
    return cursor.fetchone()


@db.connection_handler
def edit_comment(cursor, comment_id, message):
    edited_count = get_edited_count(comment_id)
    if edited_count['edited_count'] is None:
        query = """
                UPDATE comment
                SET message = %(message)s, edited_count = 1
                WHERE id = %(comment_id)s;
        """
        cursor.execute(query, {'message': message, 'comment_id': comment_id})
    else:
        ed_count = edited_count['edited_count'] + 1
        query = """
                        UPDATE comment
                        SET message = %(message)s, edited_count = %(ed_count)s
                        WHERE id = %(comment_id)s;
                """
        cursor.execute(query, {'message': message, 'comment_id': comment_id, 'ed_count': ed_count})


@db.connection_handler
def get_edited_count(cursor, comment_id):
    query = """
            SELECT edited_count FROM comment
            WHERE id = %(comment_id)s
    """
    cursor.execute(query, {'comment_id': comment_id})
    return cursor.fetchone()


@db.connection_handler
def get_question_id_by_comment(cursor, comment_id):
    query = """
            SELECT comment.id AS comment_id,
                   comment.question_id AS com_question_id,
                   answer.question_id AS ans_question_id
                   FROM comment
            LEFT JOIN answer ON comment.answer_id = answer.id
            WHERE comment.id = %(comment_id)s;
    """
    cursor.execute(query, {'comment_id': comment_id})
    comment = cursor.fetchone()
    if comment['com_question_id']:
        return comment['com_question_id']
    else:
        return comment['ans_question_id']


@db.connection_handler
def register_user(cursor, email, password):
    password_hashed = bcrypt.hashpw(password.encode("UTF-8"), bcrypt.gensalt())
    registration_date = util.get_current_timestamp()
    user = {'email': email, 'password': password_hashed, 'registration_date': registration_date}
    query = """
            INSERT INTO users (email, password, registration_date)
            VALUES (%(email)s, %(password)s, %(registration_date)s);
            SELECT id FROM users
            WHERE email = %(email)s;
    """
    cursor.execute(query, user)
    return cursor.fetchone()['id']
