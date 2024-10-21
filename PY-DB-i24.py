import mysql.connector
from mysql.connector import IntegrityError
# import a Query String parser
from urllib.parse import parse_qs
outp=""

my_form1 = """<html>
<body><h1>Insert stuff in the DB</h1>
Please fill all fields.<p>
<form action="./insert" method="GET">
<p>Title: <input type="text" name="the_title_from_form" required>
<p>Author: <input type="text" name="the_author_from_form" required>
<p>ISBN: <input type="text" name="the_isbn_from_form" required>
<p>Publisher: <input type="text" name="the_publisher_from_form" required>
<p>Year: <input type="number" name="the_year_from_form" required>
<p><input type="submit" name="Submit"></form></body>
</html>"""

my_search_or_insert_form = """
<p>Search database or add a new entry</p>
<form action="./selection" method="GET">
<input type="radio" id="search" name="action" value="search">
<label for="search">Search</label><br>
<input type="radio" id="insert" name="action" value="insert" checked>
<label for="insert">Insert</label><br><br>
<input type="submit" value="Proceed">
</form>"""

my_search_form = """<html>
<body><h1>Search the Database</h1>
You can leave fields blank to search with wildcards.<p>
<form action="./search" method="GET">
<p>Title: <input type="text" name="the_title_from_form">
<p>Author: <input type="text" name="the_author_from_form">
<p>ISBN: <input type="text" name="the_isbn_from_form">
<p>Publisher: <input type="text" name="the_publisher_from_form">
<p>Year: <input type="number" name="the_year_from_form">
<p><input type="submit" name="Submit"></form></body>
</html>"""

def show_form1():
    global my_form1
    newstr=my_form1
    return newstr

def show_search_or_insert_form():
    global my_search_or_insert_form
    return my_search_or_insert_form

def show_search_form():
    global my_search_form
    return my_search_form

class DBConfig:
    """Class to store and provide database credentials."""
    DBuser="kushalg"
    DBpass="cksclass"
    DB="kushalg$uniqueStore"
    DBtable="Books"
    DBhost ="kushalg.mysql.pythonanywhere-services.com"

    @classmethod
    def get_credentials(cls):
        return {
            "user": cls.DBuser,
            "passwd": cls.DBpass,
            "database": cls.DB,
            "table": cls.DBtable,
            "host": cls.DBhost,
        }

def dbDemo():
# This is just to see the contents of the DB
    global outp
    outp=""

    # Unpacking the credentials available in the DBConfig method
    creds = DBConfig.get_credentials()
    mydb = mysql.connector.connect(
    host=creds["host"], user=creds["user"], passwd=creds["passwd"], database=creds["database"]
    )

    outp += "<p>DB Connected...<br>"

    ##-- and create database object
    mycursor = mydb.cursor()

    ## Database is now ready for use

    ## Define the query for the DB
    query = "SELECT * FROM " + "  " + creds["table"]

    ## Execute the query
    mycursor.execute(query)

    ####### Handle Results:
    results = mycursor.fetchall()      ## Now all items retrieved from DB are in "results"
    ## Print all the results
    for row in results:
        outp += ', '.join(map(str,row))  ## join all elements of "row" mapped as strings separated by ", "
        outp += "<br>\n" ## Insert an HTML line break after each element

    mydb.close()     ## Finished; Close the DB
    outp += "<p>Demo complete<p>"

def dbSearch():
    global outp
    outp = "<h2>Search Results</h2>"

    creds = DBConfig.get_credentials()
    mydb = mysql.connector.connect(
        host=creds["host"], user=creds["user"], passwd=creds["passwd"], database=creds["database"]
    )
    
    mycursor = mydb.cursor()
    global myQueryString
    
    title = myQueryString.get('the_title_from_form', [''])[0]
    author = myQueryString.get('the_author_from_form', [''])[0]
    isbn = myQueryString.get('the_isbn_from_form', [''])[0]
    publisher = myQueryString.get('the_publisher_from_form', [''])[0]
    year = myQueryString.get('the_year_from_form', [''])[0]

    query = "SELECT * FROM " + creds["table"] + " WHERE Title LIKE %s AND Author LIKE %s AND ISBN LIKE %s AND Publisher LIKE %s AND Year LIKE %s"
    
    params = (
        f"%{title}%" if title else "%",
        f"%{author}%" if author else "%",
        f"%{isbn}%" if isbn else "%",
        f"%{publisher}%" if publisher else "%",
        year if year else "%"
    )
    
    mycursor.execute(query, params)
    results = mycursor.fetchall()

    if results:
        for row in results:
            outp += ', '.join(map(str, row)) + "<br>\n"
    else:
        outp += "<p>No records found.</p>"
    
    mydb.close()
    
def dbInsert():
    global outp
    outp = ""

    # Unpacking the credentials available in the DBConfig method
    creds = DBConfig.get_credentials()
    mydb = mysql.connector.connect(
        host=creds["host"],
        user=creds["user"],
        passwd=creds["passwd"],
        database=creds["database"]
    )

    outp += "<p>DB Connected...<br>"

    # Create database object
    mycursor = mydb.cursor()

    # Get form inputs from a user
    global myQueryString
    the_title = myQueryString['the_title_from_form'][0]
    the_author = myQueryString['the_author_from_form'][0]
    the_isbn = myQueryString['the_isbn_from_form'][0]
    the_publisher = myQueryString['the_publisher_from_form'][0]
    the_year = myQueryString['the_year_from_form'][0]

    # Define the INSERT query
    make_query = "INSERT INTO " + creds["table"] + " (Title, Author, ISBN, Publisher, Year) VALUES (%s, %s, %s, %s, %s)"
    query = (the_title, the_author, the_isbn, the_publisher, the_year)

    outp += "<p>Query is " + make_query + "<p>\n"

    try:
        # Execute the query
        mycursor.execute(make_query, query)
        mydb.commit()  # Commit the data to the DB
        outp += "<p>I am done inserting<p>"
        outp += "<p>Database viewable at <a href=\"./showDB\"><u>check the DB</u></a><p>"

    except IntegrityError as e:
        # Handle the duplicate ISBN error
        outp += "<p style='color:red;'>Error: Duplicate ISBN. Please use a unique ISBN.<p>"
        outp += "<p>Details: " + str(e) + "<p>"
        mydb.rollback()  # Rollback the transaction on error

    except Exception as e:
        # Handle any other potential errors
        outp += "<p style='color:red;'>Error: " + str(e) + "<p>"
        mydb.rollback()  # Rollback the transaction on error

    finally:
        mydb.close()  # Close the DB connection

    # Ensure that the outp variable is returned or included in the output
    return outp

### The following is the router ###

def application(environ, start_response):
    global outp
    global myQueryString
    myQueryString = parse_qs(environ.get('QUERY_STRING'))

    if environ.get('PATH_INFO') == '/':
        content = show_search_or_insert_form()
        status = '200 OK'
        ## start_response.set_cookie('userID', user)
    elif environ.get('PATH_INFO') == '/insert' :
        dbInsert()
        content = outp
        status = '200 OK'
    elif environ.get('PATH_INFO') == '/showDB' :
        dbDemo()
        content = outp
        status = '200 OK'
    elif environ.get('PATH_INFO') == '/form1' :
        content = show_form1()
        status = '200 OK'
    elif environ.get('PATH_INFO') == '/selection':
        action = myQueryString.get('action', [''])[0]
        if action == 'search':
            content = show_search_form()
            status = '200 OK'
        else:
            start_response('302 Found', [('Location','/form1')])
            return []
    elif environ.get('PATH_INFO') == '/search':
        dbSearch()
        content = outp
        status = '200 OK'
    else:
        status = '404 NOT FOUND'
        content = 'Page not found.'

    response_headers = [('Content-Type', 'text/html'), ('Content-Length', str(len(content)))]
    start_response(status, response_headers)
    yield content.encode('utf8')