import sqlite3
from pathlib import Path
from .classes import CLASSES

user_home_directory = Path.home()
DIR = user_home_directory / ".qgis"
DATABASE = DIR / "classes.db"

# Check if directory exists, if not, create it
if not DIR.exists():
    DIR.mkdir(parents=True)
def setup_database():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Check if the table exists already
    cursor.execute('''SELECT name FROM sqlite_master WHERE type='table' AND name='classes' ''')
    if not cursor.fetchone():
        # Create the table
        cursor.execute('''
        CREATE TABLE classes (
            id INTEGER PRIMARY KEY,
            class_id INTEGER,
            class TEXT NOT NULL,
            rgba TEXT NOT NULL
        )
        ''')

        # Pre-populate the table with data from CLASSES
        for item in CLASSES:
            cursor.execute('''
            INSERT INTO classes (class_id, class, rgba)
            VALUES (?, ?, ?)
            ''', (item['class_id'], item['class'], item['rgba']))

    conn.commit()
    conn.close()
def get_classes_from_db():
    """
    Retrieve the 'classes' table data from SQLite database and return as a list of dictionaries.

    Returns:
    - List[dict]: List containing dictionaries for each record in the 'classes' table.
    """

    # Connect to the database
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Execute the SELECT query
    cursor.execute("SELECT class, rgba, class_id FROM classes")
    rows = cursor.fetchall()

    # Transform rows into a list of dictionaries
    classes_list = [{"class": row[0], "rgba": row[1], "class_id": row[2]} for row in rows]

    # Close the database connection
    conn.close()

    return classes_list