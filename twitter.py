import mysql.connector
from urllib.parse import parse_qs
from http.cookies import SimpleCookie

class DBConfig:
    DBuser = "kushalg"
    DBpass = "cksclass"
    DB = "kushalg$twitter"
    DBhost = "kushalg.mysql.pythonanywhere-services.com"

    @classmethod
    def get_credentials(cls):
        return {
            "user": cls.DBuser,
            "passwd": cls.DBpass,
            "database": cls.DB,
            "host": cls.DBhost,
        }

def get_db_connection():
    creds = DBConfig.get_credentials()
    return mysql.connector.connect(
        host=creds["host"], user=creds["user"], passwd=creds["passwd"], database=creds["database"]
    )

def show_topics(subscribed_topics=None):
    """Display the list of topics in three sections: subscribed, all with subscribe option, and create new topic."""
    db = get_db_connection()
    cursor = db.cursor()
    try:
        # Ensure subscribed_topics is a list or set, even if it's None
        if subscribed_topics is None:
            subscribed_topics = []

        # Section 1: Show subscribed topics with their posts
        subscribed_content = "<h2>Your Subscribed Topics</h2>"
        if subscribed_topics:
            for topic_id in subscribed_topics:
                # Fetch the topic name
                cursor.execute("SELECT name FROM Topics WHERE id = %s", (topic_id,))
                topic_name = cursor.fetchone()

                if topic_name:
                    topic_name = topic_name[0]
                    # Fetch all posts for this topic
                    cursor.execute(
                        "SELECT content, created_at FROM Messages WHERE topic_id = %s ORDER BY created_at DESC",
                        (topic_id,)
                    )
                    messages = cursor.fetchall()

                    # Show the topic and its posts
                    subscribed_content += f"<h3>{topic_name}</h3>"
                    if messages:
                        subscribed_content += "<ul>"
                        for message, created_at in messages:
                            subscribed_content += f"<li><strong>{created_at}:</strong> {message}</li>"
                        subscribed_content += "</ul>"
                    else:
                        subscribed_content += "<p>No messages yet.</p>"

                    # Add an unsubscribe option for the subscribed topic
                    subscribed_content += f"""
                        <form action="/unsubscribe" method="POST">
                            <input type="hidden" name="topic_id" value="{topic_id}">
                            <input type="submit" value="Unsubscribe">
                        </form>
                    """
        else:
            subscribed_content += "<p>You are not subscribed to any topics.</p>"

        # Section 2: Show all topics with Subscribe option
        all_content = "<h2>All Available Topics</h2>"
        cursor.execute("SELECT id, name FROM Topics")
        all_topics = cursor.fetchall()

        if all_topics:
            all_content += "<ul>"
            for topic_id, topic_name in all_topics:
                # If the topic is not subscribed, show the subscribe button
                subscribe_button = ""
                if topic_id not in subscribed_topics:
                    subscribe_button = f'<a href="/subscribe?topic_id={topic_id}">Subscribe</a>'
                all_content += f"""
                    <li>{topic_name}
                        <a href="/view_topic?topic_id={topic_id}">View</a> |
                        {subscribe_button}
                    </li>
                """
            all_content += "</ul>"
        else:
            all_content += "<p>No topics available. Create a new one!</p>"

        # Section 3: Create a new topic
        create_content = "<h2>Create a New Topic</h2>"
        create_content += """
            <form action="/create_topic" method="POST">
                <label for="topic_name">Topic Name:</label>
                <input type="text" name="topic_name" required>
                <input type="submit" value="Create Topic">
            </form>
        """

        # Combine all sections
        content = f"""
            {subscribed_content}
            {all_content}
            {create_content}
        """

        return content
    except Exception as e:
        return f"<p>Error displaying topics: {str(e)}</p>"
    finally:
        db.close()

def create_topic(environ, start_response):
    """Create a new topic in the database."""
    length = int(environ.get('CONTENT_LENGTH', 0))
    body = environ['wsgi.input'].read(length).decode('utf-8')
    post_data = parse_qs(body)
    topic_name = post_data.get('topic_name', [None])[0]

    if not topic_name:
        content = "<p>Topic name is required.</p>"
        status = "400 Bad Request"
    else:
        db = get_db_connection()
        cursor = db.cursor()
        try:
            cursor.execute("INSERT INTO Topics (name) VALUES (%s)", (topic_name,))
            db.commit()
            content = f"<p>Topic '{topic_name}' created successfully! <a href='/'>Go back</a></p>"
            status = "201 Created"
        except Exception as e:
            content = f"<p>Error creating topic: {str(e)}</p>"
            status = "500 Internal Server Error"
        finally:
            db.close()

    response_headers = [('Content-Type', 'text/html'), ('Content-Length', str(len(content)))]
    start_response(status, response_headers)
    return [content.encode('utf-8')]


def view_topic(topic_id):
    """Display the latest 3 messages for a topic and provide actions."""
    db = get_db_connection()
    cursor = db.cursor()

    # Fetch the latest 3 messages for the topic
    cursor.execute(
        "SELECT content FROM Messages WHERE topic_id = %s ORDER BY created_at DESC LIMIT 3",
        (topic_id,)
    )
    messages = cursor.fetchall()
    db.close()

    html = f"<h1>Messages for Topic {topic_id}</h1>"
    if messages:
        html += "<ul>"
        for message in messages:
            html += f"<li>{message[0]}</li>"
        html += "</ul>"
    else:
        html += "<p>No messages found for this topic.</p>"

    # Add buttons for actions
    html += f"""
    <form action="/view_all_messages" method="GET">
        <input type="hidden" name="topic_id" value="{topic_id}">
        <input type="submit" value="View All Messages">
    </form>
    <form action="/post_message_form" method="GET">
        <input type="hidden" name="topic_id" value="{topic_id}">
        <input type="submit" value="Post a New Message">
    </form>
    """
    html += "<p><a href='/'>Go back</a></p>"

    return html

def post_message_form(environ, start_response):
    """Display a form to post a new message for a topic."""
    query = parse_qs(environ.get('QUERY_STRING', ''))
    topic_id = query.get('topic_id', [None])[0]

    if not topic_id:
        content = "<p>Invalid topic ID.</p>"
        status = '400 Bad Request'
    else:
        content = f"""
        <h1>Post a New Message</h1>
        <form action="/post_message" method="POST">
            <input type="hidden" name="topic_id" value="{topic_id}">
            <p>Message: <textarea name="message_content" required></textarea></p>
            <input type="submit" value="Post Message">
        </form>
        """
        status = '200 OK'

    response_headers = [('Content-Type', 'text/html'), ('Content-Length', str(len(content)))]
    start_response(status, response_headers)
    return [content.encode('utf-8')]

def post_message(environ, start_response):
    """Handle posting a new message to a topic."""
    length = int(environ.get('CONTENT_LENGTH', 0))
    body = environ['wsgi.input'].read(length).decode('utf-8')
    post_data = parse_qs(body)

    topic_id = post_data.get('topic_id', [None])[0]
    message_content = post_data.get('message_content', [None])[0]

    if not topic_id or not message_content:
        content = "<p>Both topic ID and message content are required.</p>"
        status = '400 Bad Request'
    else:
        db = get_db_connection()
        cursor = db.cursor()
        try:
            cursor.execute(
                "INSERT INTO Messages (topic_id, content, created_at) VALUES (%s, %s, NOW())",
                (topic_id, message_content)
            )
            db.commit()
            content = f"<p>Message posted successfully! <a href='/view_topic?topic_id={topic_id}'>Go back</a></p>"
            status = '201 Created'
        except Exception as e:
            content = f"<p>Error posting message: {str(e)}</p>"
            status = '500 Internal Server Error'
        finally:
            db.close()

    response_headers = [('Content-Type', 'text/html'), ('Content-Length', str(len(content)))]
    start_response(status, response_headers)
    return [content.encode('utf-8')]


def subscribe(environ, start_response):
    """Subscribe a user to a topic."""
    query = parse_qs(environ.get('QUERY_STRING', ''))
    topic_id = query.get('topic_id', [None])[0]

    if not topic_id:
        content = "<p>Invalid topic ID.</p>"
        status = '400 Bad Request'
    else:
        # Get the current subscriptions from the user's cookie
        cookie = SimpleCookie(environ.get('HTTP_COOKIE', ''))
        subscribed_topics = set()

        if 'subscribed_topics' in cookie:
            subscribed_topics = set(map(int, cookie['subscribed_topics'].value.split(',')))

        # Add the new topic to the set of subscribed topics
        subscribed_topics.add(int(topic_id))

        # Create a response to update the cookie
        content = f"<p>Subscribed to Topic {topic_id} successfully.</p>"
        content += '<p><a href="/">Go back</a></p>'
        status = '200 OK'
        response_headers = [
            ('Content-Type', 'text/html'),
            ('Content-Length', str(len(content))),
        ]

        # Set the updated cookie with a 30-day expiry
        new_cookie = SimpleCookie()
        new_cookie['subscribed_topics'] = ','.join(map(str, subscribed_topics))
        new_cookie['subscribed_topics']['path'] = '/'
        new_cookie['subscribed_topics']['max-age'] = 30 * 24 * 60 * 60  # 30 days

        for key, morsel in new_cookie.items():
            response_headers.append(('Set-Cookie', morsel.OutputString()))

        start_response(status, response_headers)
        return [content.encode('utf-8')]

    # Return error response if something goes wrong
    response_headers = [('Content-Type', 'text/html'), ('Content-Length', str(len(content)))]
    start_response(status, response_headers)
    return [content.encode('utf-8')]

def unsubscribe(environ, start_response):
    """Unsubscribe a user from a topic."""
    # Get the topic ID from the form data
    length = int(environ.get('CONTENT_LENGTH', 0))
    body = environ['wsgi.input'].read(length).decode('utf-8')
    post_data = parse_qs(body)
    topic_id = post_data.get('topic_id', [None])[0]

    if not topic_id:
        content = "<p>Invalid topic ID.</p>"
        status = '400 Bad Request'
    else:
        # Get the current subscriptions from the user's cookie
        cookie = SimpleCookie(environ.get('HTTP_COOKIE', ''))
        subscribed_topics = set()

        if 'subscribed_topics' in cookie:
            subscribed_topics = set(map(int, cookie['subscribed_topics'].value.split(',')))

        # Remove the topic from the subscribed topics
        subscribed_topics.discard(int(topic_id))

        # Create a response to update the cookie
        content = f"<p>Unsubscribed from Topic {topic_id} successfully.</p>"
        content += '<p><a href="/">Go back</a></p>'

        status = '200 OK'
        response_headers = [
            ('Content-Type', 'text/html'),
            ('Content-Length', str(len(content))),
        ]

        # Set the updated cookie with a 30-day expiry
        new_cookie = SimpleCookie()
        new_cookie['subscribed_topics'] = ','.join(map(str, subscribed_topics))
        new_cookie['subscribed_topics']['path'] = '/'
        new_cookie['subscribed_topics']['max-age'] = 30 * 24 * 60 * 60  # 30 days

        for key, morsel in new_cookie.items():
            response_headers.append(('Set-Cookie', morsel.OutputString()))

        start_response(status, response_headers)
        return [content.encode('utf-8')]

    # Return error response if something goes wrong
    response_headers = [('Content-Type', 'text/html'), ('Content-Length', str(len(content)))]
    start_response(status, response_headers)
    return [content.encode('utf-8')]



def view_all_messages(environ, start_response):
    """Display all messages for a given topic."""
    query = parse_qs(environ.get('QUERY_STRING', ''))
    topic_id = query.get('topic_id', [None])[0]

    if not topic_id:
        content = "<p>Invalid topic ID.</p>"
        status = '400 Bad Request'
    else:
        db = get_db_connection()
        cursor = db.cursor()
        try:
            cursor.execute(
                "SELECT content, created_at FROM Messages WHERE topic_id = %s ORDER BY created_at DESC",
                (topic_id,)
            )
            messages = cursor.fetchall()

            if messages:
                content = f"<h1>All Messages for Topic {topic_id}</h1><ul>"
                for message, created_at in messages:
                    content += f"<li><strong>{created_at}:</strong> {message}</li>"
                content += "</ul>"
            else:
                content = f"<p>No messages found for Topic {topic_id}.</p>"

            status = '200 OK'
        except Exception as e:
            content = f"<p>Error retrieving messages: {str(e)}</p>"
            status = '500 Internal Server Error'
        finally:
            db.close()

    response_headers = [('Content-Type', 'text/html'), ('Content-Length', str(len(content)))]
    start_response(status, response_headers)
    return [content.encode('utf-8')]


def application(environ, start_response):
    path = environ.get('PATH_INFO', '/')
    query = parse_qs(environ.get('QUERY_STRING', ''))
    cookie = SimpleCookie(environ.get('HTTP_COOKIE', ''))

    if path == '/':
        subscribed_topics = cookie.get('subscribed_topics')
        print("subscribed", subscribed_topics)
        try:
            if subscribed_topics:
                subscribed_topics = set(map(int, subscribed_topics.value.split(',')))
        except ValueError:
            subscribed_topics = None
        content = show_topics(subscribed_topics)
        status = '200 OK'

    elif path == '/create_topic' and environ.get('REQUEST_METHOD') == 'POST':
        return create_topic(environ, start_response)

    elif path == '/subscribe' and environ.get('REQUEST_METHOD') in ['GET', 'POST']:
        return subscribe(environ, start_response)

    elif path == '/unsubscribe' and environ.get('REQUEST_METHOD') == 'POST':
        return unsubscribe(environ, start_response)

    elif path == '/view_topic':
        topic_id = query.get('topic_id', [None])[0]
        if topic_id:
            content = view_topic(int(topic_id))
            status = '200 OK'
        else:
            content = "<p>Invalid topic ID.</p>"
            status = '400 Bad Request'

    elif path == '/view_all_messages':
        return view_all_messages(environ, start_response)

    elif path == '/post_message_form':
        return post_message_form(environ, start_response)

    elif path == '/post_message' and environ.get('REQUEST_METHOD') == 'POST':
        return post_message(environ, start_response)

    else:
        content = "<p>Page not found.</p>"
        status = '404 Not Found'

    response_headers = [('Content-Type', 'text/html'), ('Content-Length', str(len(content)))]
    start_response(status, response_headers)
    return [content.encode('utf-8')]
