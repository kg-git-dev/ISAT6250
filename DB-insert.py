import mysql.connector
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


class DBConfig:
    """Class to store and provide database credentials."""
    DBuser="kushalg"
    DBpass="cksclass"
    DB="kushalg$Bookstore"
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


def show_form1():
    global my_form1
    newstr=my_form1
    return newstr


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


def dbInsert():
# This function is to insert records in the database'
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

    ## Get form inputs from a user
    global myQueryString
    the_title  = myQueryString['the_title_from_form'][0]
    the_author = myQueryString['the_author_from_form'][0]
    the_isbn = myQueryString['the_isbn_from_form'][0]
    the_publisher = myQueryString['the_publisher_from_form'][0]
    the_year = myQueryString['the_year_from_form'][0]

    ## Define a query for the DB, possibly using form inputs from a user.
    ## An INSERT query must be formatted like this:
    ## INSERT INTO Books (Title, Author, ISBN, Publisher, Year) VALUES ('Book Title', 'Leon', '152347', 'SomePublisher','2020')
    ## i.e. with the \'

    # In this trick, the make_query is just a general form with
    # placeholders which are then substituted using the .format method
    make_query = "INSERT INTO " + creds["table"] + " (Title, Author, ISBN, Publisher, Year) VALUES (\'{}\', \'{}\', \'{}\', \'{}\', \'{}\')"
    query = make_query.format(the_title,the_author,the_isbn,the_publisher,the_year)

    outp += "<p>Query is " + query + "<p>\n"

    ## Execute the query
    mycursor.execute(query)

    mydb.commit()  ## This is needed to commit the data to the DB

    mydb.close()     ## Finished; Close the DB
    outp += "<p>I am done inserting<p>"


### The following is the router ###

def application(environ, start_response):
    global outp
    global myQueryString
    myQueryString = parse_qs(environ.get('QUERY_STRING'))

    if environ.get('PATH_INFO') == '/':
        status = '200 OK'
        content = "HELLO_WORLD"
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
    else:
        status = '404 NOT FOUND'
        content = 'Page not found.'

    response_headers = [('Content-Type', 'text/html'), ('Content-Length', str(len(content)))]
    start_response(status, response_headers)
    yield content.encode('utf8')
