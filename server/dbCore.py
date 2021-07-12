import sqlite3

def drop_table():
	with sqlite3.connect('annotations.db') as connection:
		c = connection.cursor()
		c.execute("""DROP TABLE IF EXISTS documents;""")
		c.execute("""DROP TABLE IF EXISTS annotations;""")
		c.execute("""DROP TABLE IF EXISTS labels;""")
		c.execute("""DROP TABLE IF EXISTS sections;""")
		c.execute("""DROP TABLE IF EXISTS recommendations;""")
		c.execute("""DROP TABLE IF EXISTS users;""")
	return True

def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Exception as e:
        print(e)
 
    return conn

def create_table(conn, create_table_sql):
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Exception as e:
        print(e)

def main():
	database = 'annotations.db'

	createDocumentsTable = """CREATE TABLE documents(
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		name TEXT NOT NULL,
		owner INTEGER NOT NULL,
		lastChanged TIMESTAMP NOT NULL,
		inputType INTEGER NOT NULL,
		unitOfAnalysis INTEGER NOT NULL,
		language TEXT
		);
		"""

	createAnnotationsTable = """CREATE TABLE annotations(
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		documentID INTEGER NOT NULL,
		conversation TEXT,
		attribute TEXT,
		annotationID TEXT NOT NULL,
		document TEXT NOT NULL,
		start INTEGER NOT NULL,
		length INTEGER NOT NULL,
		label TEXT NOT NULL,
		isRecommendation INTEGER NOT NULL,
		sectionLink INTEGER NOT NULL,
		matchHighlight TEXT,
		confidence INTEGER
		);
		"""

	createLabelsTable = """CREATE TABLE labels(
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		documentID INTEGER NOT NULL,
		label TEXT NOT NULL,
		color TEXT NOT NULL,
		codeRule TEXT
		);
		"""

	createSectionsTable = """CREATE TABLE sections(
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		documentID INTEGER NOT NULL,
		conversation TEXT,
		attribute TEXT,
		section TEXT NOT NULL,
		label TEXT NOT NULL,
		isRecommendation INTEGER NOT NULL
		);
		"""

	createRecommendationsTable = """CREATE TABLE recommendations(
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		documentID INTEGER NOT NULL,
		sectionID INTEGER NOT NULL,
		annotationID TEXT,
		labelCR TEXT,
		labelMR TEXT,
		confidence INTEGER NOT NULL,
		deletionFlag INTEGER NOT NULL,
		ruleHighlight TEXT
		);
		"""

	createUsersTable = """CREATE TABLE users(
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		email Text NOT NULL UNIQUE,
		password varchar(255) NOT NULL
		);
		"""

	drop_table()
	
	conn = create_connection(database)

	# create tables
	if conn is not None:
		#create Annotations table
		create_table(conn, createDocumentsTable)
		#create Annotations table
		create_table(conn, createAnnotationsTable)
		#create Labels table
		create_table(conn, createLabelsTable)
		#create Sections table
		create_table(conn, createSectionsTable)
		#create Recommendations table
		create_table(conn, createRecommendationsTable)
		#create Users table
		create_table(conn, createUsersTable)
	else:
		print("Error! Cannot create the database connection.")

if __name__ == '__main__':
	main()
	



	