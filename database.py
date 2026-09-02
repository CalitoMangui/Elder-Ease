import sqlite3


DATABASE = "elder_ease.db"


def get_db_connection():

    connection = sqlite3.connect(DATABASE)

    connection.row_factory = sqlite3.Row

    return connection


def create_tables():

    connection = get_db_connection()

    cursor = connection.cursor()


    # =====================================================
    # SHELTERS / HOMES TABLE
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS shelters (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            email TEXT UNIQUE NOT NULL,

            password TEXT NOT NULL,

            phone TEXT,

            address TEXT,

            home_code TEXT UNIQUE,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )
    """)


    # =====================================================
    # ELDER USERS TABLE
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            email TEXT UNIQUE NOT NULL,

            password TEXT NOT NULL,

            phone TEXT,

            age INTEGER,

            location TEXT,

            shelter_id INTEGER,

            shelter_status TEXT DEFAULT 'none'

        )
    """)


    # =====================================================
    # ACTIVITIES TABLE
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activities (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            shelter_id INTEGER,

            name TEXT NOT NULL,

            date TEXT NOT NULL,

            time TEXT NOT NULL,

            location TEXT NOT NULL,

            description TEXT NOT NULL,

            participants INTEGER NOT NULL,

            FOREIGN KEY (shelter_id)
                REFERENCES shelters(id)

        )
    """)


    # =====================================================
    # NOTIFICATIONS TABLE
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            shelter_id INTEGER,

            message TEXT NOT NULL,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            is_read INTEGER DEFAULT 0,

            FOREIGN KEY (shelter_id)
                REFERENCES shelters(id)

        )
    """)


    # =====================================================
    # COMMUNITY POSTS TABLE
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS community_posts (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER,

            content TEXT NOT NULL,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (user_id)
                REFERENCES users(id)

        )
    """)


    # =====================================================
    # POST LIKES TABLE
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS post_likes (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            post_id INTEGER NOT NULL,

            user_id INTEGER NOT NULL,

            FOREIGN KEY (post_id)
                REFERENCES community_posts(id),

            FOREIGN KEY (user_id)
                REFERENCES users(id),

            UNIQUE(post_id, user_id)

        )
    """)


    # =====================================================
    # POST COMMENTS TABLE
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS post_comments (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            post_id INTEGER NOT NULL,

            user_id INTEGER NOT NULL,

            content TEXT NOT NULL,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (post_id)
                REFERENCES community_posts(id),

            FOREIGN KEY (user_id)
                REFERENCES users(id)

        )
    """)


    # =====================================================
    # ACTIVITY PARTICIPANTS TABLE
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activity_participants (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            activity_id INTEGER NOT NULL,

            user_id INTEGER NOT NULL,

            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (activity_id)
                REFERENCES activities(id),

            FOREIGN KEY (user_id)
                REFERENCES users(id),

            UNIQUE(activity_id, user_id)

        )
    """)


    # =====================================================
    # EMERGENCY CONTACTS TABLE
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS emergency_contacts (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            name TEXT NOT NULL,

            relationship TEXT NOT NULL,

            phone TEXT NOT NULL,

            FOREIGN KEY (user_id)
                REFERENCES users(id)

        )
    """)


    # =====================================================
    # TRUSTED CONTACTS TABLE
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trusted_contacts (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            name TEXT NOT NULL,

            relationship TEXT NOT NULL,

            phone TEXT NOT NULL,

            FOREIGN KEY (user_id)
                REFERENCES users(id)

        )
    """)


    # =====================================================
    # SOS ALERTS TABLE
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sos_alerts (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            message TEXT NOT NULL,

            location TEXT,

            alert_token TEXT UNIQUE NOT NULL,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (user_id)
                REFERENCES users(id)

        )
    """)


    # =====================================================
    # UPDATE OLDER USERS DATABASE
    # =====================================================

    try:

        cursor.execute("""
            ALTER TABLE users
            ADD COLUMN phone TEXT
        """)

    except sqlite3.OperationalError:

        pass


    try:

        cursor.execute("""
            ALTER TABLE users
            ADD COLUMN age INTEGER
        """)

    except sqlite3.OperationalError:

        pass


    try:

        cursor.execute("""
            ALTER TABLE users
            ADD COLUMN location TEXT
        """)

    except sqlite3.OperationalError:

        pass


    try:

        cursor.execute("""
            ALTER TABLE users
            ADD COLUMN shelter_id INTEGER
        """)

    except sqlite3.OperationalError:

        pass


    try:

        cursor.execute("""
            ALTER TABLE users
            ADD COLUMN shelter_status TEXT DEFAULT 'none'
        """)

    except sqlite3.OperationalError:

        pass


    # =====================================================
    # UPDATE OLDER SHELTER DATABASE
    # =====================================================

    try:

        cursor.execute("""
            ALTER TABLE shelters
            ADD COLUMN phone TEXT
        """)

    except sqlite3.OperationalError:

        pass


    try:

        cursor.execute("""
            ALTER TABLE shelters
            ADD COLUMN address TEXT
        """)

    except sqlite3.OperationalError:

        pass


    try:

        cursor.execute("""
            ALTER TABLE shelters
            ADD COLUMN home_code TEXT
        """)

    except sqlite3.OperationalError:

        pass


    # =====================================================
    # UPDATE OLDER SOS DATABASE
    # =====================================================

    try:

        cursor.execute("""
            ALTER TABLE sos_alerts
            ADD COLUMN alert_token TEXT
        """)

    except sqlite3.OperationalError:

        pass


    # =====================================================
    # SHELTER CONNECTION REQUESTS TABLE
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS shelter_requests (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            shelter_id INTEGER NOT NULL,

            status TEXT DEFAULT 'pending',

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (user_id)
                REFERENCES users(id),

            FOREIGN KEY (shelter_id)
                REFERENCES shelters(id)

        )
    """)

    connection.commit()

    connection.close()