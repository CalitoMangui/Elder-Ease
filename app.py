from flask import Flask, render_template, request, session, redirect, url_for
import secrets
import sqlite3
from database import create_tables, get_db_connection


app = Flask(__name__)

app.secret_key = "elder-ease-secret-key"


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return render_template("index.html")


# =========================================================
# ELDER LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        connection = get_db_connection()

        user = connection.execute(
            """
            SELECT *
            FROM users
            WHERE email = ?
            AND password = ?
            """,
            (
                email,
                password
            )
        ).fetchone()

        connection.close()

        if user:

            session["user_id"] = user["id"]
            session["user_name"] = user["name"]

            return render_template(
                "dashboard.html",
                user=user
            )

        return render_template(
            "login.html",
            message="Invalid email or password."
        )

    return render_template("login.html")


# =========================================================
# ELDER REGISTRATION
# =========================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]
        age = request.form["age"]
        location = request.form["location"]
        password = request.form["password"]

        lives_in_home = request.form.get("lives_in_home")
        home_code = request.form.get("home_code", "").strip().upper()

        connection = get_db_connection()

        try:

            shelter_id = None
            shelter_status = "none"

            if lives_in_home == "yes":

                if not home_code:

                    connection.close()

                    return render_template(
                        "register.html",
                        message="Please enter your Home Code."
                    )

                shelter = connection.execute(
                    """
                    SELECT id
                    FROM shelters
                    WHERE home_code = ?
                    """,
                    (home_code,)
                ).fetchone()

                if not shelter:

                    connection.close()

                    return render_template(
                        "register.html",
                        message="The Home Code is not valid. Please check the code with your registered home."
                    )

                shelter_id = shelter["id"]
                shelter_status = "pending"

            cursor = connection.execute(
                """
                INSERT INTO users
                (
                    name,
                    email,
                    password,
                    phone,
                    age,
                    location,
                    shelter_id,
                    shelter_status
                )

                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    name,
                    email,
                    password,
                    phone,
                    age,
                    location,
                    shelter_id,
                    shelter_status
                )
            )

            user_id = cursor.lastrowid

            if lives_in_home == "yes":

                connection.execute(
                    """
                    INSERT INTO shelter_requests
                    (
                        user_id,
                        shelter_id,
                        status
                    )

                    VALUES (?, ?, 'pending')
                    """,
                    (
                        user_id,
                        shelter_id
                    )
                )

            connection.commit()
            connection.close()

            if lives_in_home == "yes":

                return render_template(
                    "login.html",
                    message=(
                        "Account created successfully! "
                        "Your Home connection request has been sent to the shelter. "
                        "Please log in."
                    )
                )

            return render_template(
                "login.html",
                message="Account created successfully! Please log in."
            )

        except sqlite3.IntegrityError:

            connection.rollback()
            connection.close()

            return render_template(
                "register.html",
                message="This email is already registered."
            )

        except Exception as error:

            connection.rollback()
            connection.close()

            print("ELDER REGISTRATION ERROR:", error)

            return render_template(
                "register.html",
                message="Something went wrong while creating your account."
            )

    return render_template("register.html")


# =========================================================
# SHELTER LOGIN
# =========================================================

@app.route("/shelter-login", methods=["GET", "POST"])
def shelter_login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        connection = get_db_connection()

        shelter = connection.execute(
            """
            SELECT *
            FROM shelters
            WHERE email = ?
            AND password = ?
            """,
            (
                email,
                password
            )
        ).fetchone()

        connection.close()

        if shelter:

            session["shelter_id"] = shelter["id"]
            session["shelter_name"] = shelter["shelter_name"]

            return render_template(
                "shelter_dashboard.html",
                shelter=shelter
            )

        return render_template(
            "shelter_login.html",
            message="Incorrect email or password."
        )

    return render_template("shelter_login.html")


# =========================================================
# SHELTER DASHBOARD
# =========================================================

@app.route("/shelter-dashboard")
def shelter_dashboard():

    if "shelter_id" not in session:

        return redirect(url_for("shelter_login"))

    connection = get_db_connection()

    shelter = connection.execute(
        """
        SELECT *
        FROM shelters
        WHERE id = ?
        """,
        (session["shelter_id"],)
    ).fetchone()

    connection.close()

    if not shelter:

        return redirect(url_for("shelter_login"))

    return render_template(
        "shelter_dashboard.html",
        shelter=shelter
    )


# =========================================================
# SHELTER REGISTRATION
# =========================================================

@app.route("/shelter-register", methods=["GET", "POST"])
def shelter_register():

    if request.method == "POST":

        shelter_name = request.form["shelter_name"]
        email = request.form["email"]
        phone = request.form["phone"]
        address = request.form["address"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:

            return render_template(
                "shelter_register.html",
                message="Passwords do not match."
            )

        connection = get_db_connection()

        try:

            while True:

                home_code = (
                    shelter_name[:3].upper()
                    + str(secrets.randbelow(900) + 100)
                )

                existing_home = connection.execute(
                    """
                    SELECT id
                    FROM shelters
                    WHERE home_code = ?
                    """,
                    (home_code,)
                ).fetchone()

                if not existing_home:
                    break

            connection.execute(
                """
                INSERT INTO shelters
                (
                    shelter_name,
                    email,
                    phone,
                    address,
                    password,
                    home_code
                )

                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    shelter_name,
                    email,
                    phone,
                    address,
                    password,
                    home_code
                )
            )

            connection.commit()
            connection.close()

            return render_template(
                "shelter_login.html",
                message=(
                    "Shelter registered successfully! "
                    "Your Home Code is: "
                    + home_code
                    + ". Please keep this code safe."
                )
            )

        except sqlite3.IntegrityError:

            connection.rollback()
            connection.close()

            return render_template(
                "shelter_register.html",
                message="This email is already registered."
            )

        except Exception as error:

            connection.rollback()
            connection.close()

            print("SHELTER REGISTRATION ERROR:", error)

            return render_template(
                "shelter_register.html",
                message="Something went wrong while creating the shelter account."
            )

    return render_template("shelter_register.html")


# =========================================================
# ELDER DASHBOARD
# =========================================================

@app.route("/dashboard")
def dashboard():

    return render_template("dashboard.html")


# =========================================================
# ELDER PROFILE
# =========================================================

@app.route("/profile")
def profile():

    if "user_id" not in session:

        return redirect(url_for("login"))

    connection = get_db_connection()

    user = connection.execute(
        """
        SELECT
            users.*,
            shelters.shelter_name,
            shelters.email AS shelter_email,
            shelters.phone AS shelter_phone,
            shelters.address AS shelter_address
        FROM users

        LEFT JOIN shelters
            ON users.shelter_id = shelters.id

        WHERE users.id = ?
        """,
        (session["user_id"],)
    ).fetchone()

    connection.close()

    if not user:

        return redirect(url_for("login"))

    return render_template(
        "profile.html",
        user=user
    )


# =========================================================
# EDIT ELDER PROFILE
# =========================================================

@app.route("/edit-profile", methods=["GET", "POST"])
def edit_profile():

    if "user_id" not in session:

        return redirect(url_for("login"))

    connection = get_db_connection()

    user = connection.execute(
        """
        SELECT *
        FROM users
        WHERE id = ?
        """,
        (session["user_id"],)
    ).fetchone()

    if request.method == "POST":

        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        age = request.form.get("age")
        location = request.form.get("location")

        connection.execute(
            """
            UPDATE users
            SET
                name = ?,
                email = ?,
                phone = ?,
                age = ?,
                location = ?
            WHERE id = ?
            """,
            (
                name,
                email,
                phone,
                age,
                location,
                session["user_id"]
            )
        )

        connection.commit()
        connection.close()

        return redirect(url_for("profile"))

    connection.close()

    return render_template(
        "edit_profile.html",
        user=user
    )


# =========================================================
# ELDER COMMUNITY
# =========================================================

@app.route("/community")
def community():

    connection = get_db_connection()

    posts = connection.execute(
        """
        SELECT
            community_posts.id,
            community_posts.user_id,
            community_posts.content,
            community_posts.created_at,
            users.name,
            COUNT(DISTINCT post_likes.id) AS like_count

        FROM community_posts

        JOIN users
            ON community_posts.user_id = users.id

        LEFT JOIN post_likes
            ON community_posts.id = post_likes.post_id

        GROUP BY community_posts.id

        ORDER BY community_posts.created_at DESC
        """
    ).fetchall()

    comments = connection.execute(
        """
        SELECT
            post_comments.id,
            post_comments.post_id,
            post_comments.user_id,
            post_comments.content,
            post_comments.created_at,
            users.name

        FROM post_comments

        JOIN users
            ON post_comments.user_id = users.id

        ORDER BY post_comments.created_at ASC
        """
    ).fetchall()

    connection.close()

    return render_template(
        "community.html",
        posts=posts,
        comments=comments
    )


# =========================================================
# CREATE POST
# =========================================================

@app.route("/create-post", methods=["GET", "POST"])
def create_post():

    if "user_id" not in session:

        return render_template(
            "login.html",
            message="Please log in first."
        )

    if request.method == "POST":

        content = request.form["content"]

        connection = get_db_connection()

        connection.execute(
            """
            INSERT INTO community_posts
            (user_id, content)

            VALUES (?, ?)
            """,
            (
                session["user_id"],
                content
            )
        )

        connection.commit()
        connection.close()

        return redirect(url_for("community"))

    return render_template("create_post.html")


# =========================================================
# LIKE POST
# =========================================================

@app.route("/like-post/<int:post_id>", methods=["POST"])
def like_post(post_id):

    if "user_id" not in session:

        return redirect(url_for("login"))

    connection = get_db_connection()

    existing_like = connection.execute(
        """
        SELECT id
        FROM post_likes
        WHERE post_id = ?
        AND user_id = ?
        """,
        (
            post_id,
            session["user_id"]
        )
    ).fetchone()

    if existing_like:

        connection.execute(
            """
            DELETE FROM post_likes
            WHERE post_id = ?
            AND user_id = ?
            """,
            (
                post_id,
                session["user_id"]
            )
        )

    else:

        connection.execute(
            """
            INSERT INTO post_likes
            (post_id, user_id)

            VALUES (?, ?)
            """,
            (
                post_id,
                session["user_id"]
            )
        )

    connection.commit()
    connection.close()

    return redirect(url_for("community"))


# =========================================================
# COMMENT
# =========================================================

@app.route("/comment/<int:post_id>", methods=["GET", "POST"])
def comment_post(post_id):

    if "user_id" not in session:

        return redirect(url_for("login"))

    connection = get_db_connection()

    post = connection.execute(
        """
        SELECT
            community_posts.id,
            community_posts.content,
            users.name

        FROM community_posts

        JOIN users
            ON community_posts.user_id = users.id

        WHERE community_posts.id = ?
        """,
        (post_id,)
    ).fetchone()

    if not post:

        connection.close()

        return "Post not found."

    if request.method == "POST":

        content = request.form["content"]

        connection.execute(
            """
            INSERT INTO post_comments
            (post_id, user_id, content)

            VALUES (?, ?, ?)
            """,
            (
                post_id,
                session["user_id"],
                content
            )
        )

        connection.commit()
        connection.close()

        return redirect(url_for("community"))

    connection.close()

    return render_template(
        "comment.html",
        post=post
    )


# =========================================================
# DELETE POST
# =========================================================

@app.route("/delete-post/<int:post_id>", methods=["POST"])
def delete_post(post_id):

    if "user_id" not in session:

        return redirect(url_for("login"))

    connection = get_db_connection()

    post = connection.execute(
        """
        SELECT id
        FROM community_posts
        WHERE id = ?
        AND user_id = ?
        """,
        (
            post_id,
            session["user_id"]
        )
    ).fetchone()

    if not post:

        connection.close()

        return "You can only delete your own posts."

    connection.execute(
        """
        DELETE FROM post_comments
        WHERE post_id = ?
        """,
        (post_id,)
    )

    connection.execute(
        """
        DELETE FROM post_likes
        WHERE post_id = ?
        """,
        (post_id,)
    )

    connection.execute(
        """
        DELETE FROM community_posts
        WHERE id = ?
        AND user_id = ?
        """,
        (
            post_id,
            session["user_id"]
        )
    )

    connection.commit()
    connection.close()

    return redirect(url_for("community"))


# =========================================================
# DELETE COMMENT
# =========================================================

@app.route("/delete-comment/<int:comment_id>", methods=["POST"])
def delete_comment(comment_id):

    if "user_id" not in session:

        return redirect(url_for("login"))

    connection = get_db_connection()

    comment = connection.execute(
        """
        SELECT id
        FROM post_comments
        WHERE id = ?
        AND user_id = ?
        """,
        (
            comment_id,
            session["user_id"]
        )
    ).fetchone()

    if not comment:

        connection.close()

        return "You can only delete your own comments."

    connection.execute(
        """
        DELETE FROM post_comments
        WHERE id = ?
        AND user_id = ?
        """,
        (
            comment_id,
            session["user_id"]
        )
    )

    connection.commit()
    connection.close()

    return redirect(url_for("community"))


# =========================================================
# EDIT POST
# =========================================================

@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
def edit_post(post_id):

    if "user_id" not in session:

        return redirect(url_for("login"))

    connection = get_db_connection()

    post = connection.execute(
        """
        SELECT
            id,
            content,
            user_id

        FROM community_posts

        WHERE id = ?
        AND user_id = ?
        """,
        (
            post_id,
            session["user_id"]
        )
    ).fetchone()

    if not post:

        connection.close()

        return "You can only edit your own posts."

    if request.method == "POST":

        content = request.form["content"]

        connection.execute(
            """
            UPDATE community_posts
            SET content = ?
            WHERE id = ?
            AND user_id = ?
            """,
            (
                content,
                post_id,
                session["user_id"]
            )
        )

        connection.commit()
        connection.close()

        return redirect(url_for("community"))

    connection.close()

    return render_template(
        "edit_post.html",
        post=post
    )


# =========================================================
# HELP & SAFETY
# =========================================================

@app.route("/help")
def help_page():

    if "user_id" not in session:

        return redirect(url_for("login"))

    return render_template("help.html")


# =========================================================
# EMERGENCY CONTACTS
# =========================================================

@app.route("/emergency-contacts")
def emergency_contacts():

    if "user_id" not in session:

        return redirect(url_for("login"))

    connection = get_db_connection()

    contacts = connection.execute(
        """
        SELECT *
        FROM emergency_contacts
        WHERE user_id = ?
        ORDER BY name ASC
        """,
        (session["user_id"],)
    ).fetchall()

    connection.close()

    return render_template(
        "emergency_contacts.html",
        contacts=contacts
    )


# =========================================================
# ADD EMERGENCY CONTACT
# =========================================================

@app.route("/add-emergency-contact", methods=["POST"])
def add_emergency_contact():

    if "user_id" not in session:

        return redirect(url_for("login"))

    name = request.form["name"]
    relationship = request.form["relationship"]
    phone = request.form["phone"]

    connection = get_db_connection()

    connection.execute(
        """
        INSERT INTO emergency_contacts
        (
            user_id,
            name,
            relationship,
            phone
        )

        VALUES (?, ?, ?, ?)
        """,
        (
            session["user_id"],
            name,
            relationship,
            phone
        )
    )

    connection.commit()
    connection.close()

    return redirect(url_for("emergency_contacts"))


# =========================================================
# DELETE EMERGENCY CONTACT
# =========================================================

@app.route("/delete-emergency-contact/<int:contact_id>", methods=["POST"])
def delete_emergency_contact(contact_id):

    if "user_id" not in session:

        return redirect(url_for("login"))

    connection = get_db_connection()

    connection.execute(
        """
        DELETE FROM emergency_contacts
        WHERE id = ?
        AND user_id = ?
        """,
        (
            contact_id,
            session["user_id"]
        )
    )

    connection.commit()
    connection.close()

    return redirect(url_for("emergency_contacts"))


# =========================================================
# HEALTHCARE SUPPORT
# =========================================================

@app.route("/healthcare")
def healthcare():

    if "user_id" not in session:

        return redirect(url_for("login"))

    return render_template("healthcare.html")


# =========================================================
# TRUSTED CONTACT
# =========================================================

@app.route("/trusted-contact")
def trusted_contact():

    if "user_id" not in session:

        return redirect(url_for("login"))

    connection = get_db_connection()

    contacts = connection.execute(
        """
        SELECT *
        FROM trusted_contacts
        WHERE user_id = ?
        ORDER BY name ASC
        """,
        (session["user_id"],)
    ).fetchall()

    connection.close()

    return render_template(
        "trusted_contact.html",
        contacts=contacts
    )


# =========================================================
# ADD TRUSTED CONTACT
# =========================================================

@app.route("/add-trusted-contact", methods=["POST"])
def add_trusted_contact():

    if "user_id" not in session:

        return redirect(url_for("login"))

    name = request.form["name"]
    relationship = request.form["relationship"]
    phone = request.form["phone"]

    connection = get_db_connection()

    connection.execute(
        """
        INSERT INTO trusted_contacts
        (
            user_id,
            name,
            relationship,
            phone
        )

        VALUES (?, ?, ?, ?)
        """,
        (
            session["user_id"],
            name,
            relationship,
            phone
        )
    )

    connection.commit()
    connection.close()

    return redirect(url_for("trusted_contact"))


# =========================================================
# DELETE TRUSTED CONTACT
# =========================================================

@app.route("/delete-trusted-contact/<int:contact_id>", methods=["POST"])
def delete_trusted_contact(contact_id):

    if "user_id" not in session:

        return redirect(url_for("login"))

    connection = get_db_connection()

    connection.execute(
        """
        DELETE FROM trusted_contacts
        WHERE id = ?
        AND user_id = ?
        """,
        (
            contact_id,
            session["user_id"]
        )
    )

    connection.commit()
    connection.close()

    return redirect(url_for("trusted_contact"))


# =========================================================
# SCAM ALERT
# =========================================================

@app.route("/scam-alert")
def scam_alert():

    if "user_id" not in session:

        return redirect(url_for("login"))

    return render_template("scam_alert.html")


# =========================================================
# ELDER-EASE SUPPORT
# =========================================================

@app.route("/elder-ease-support")
def elder_ease_support():

    if "user_id" not in session:

        return redirect(url_for("login"))

    return render_template("elder_ease_support.html")


# =========================================================
# ACTIVITIES
# =========================================================

@app.route("/activities")
def activities():

    if "user_id" not in session:

        return redirect(url_for("login"))

    connection = get_db_connection()

    activities = connection.execute(
        """
        SELECT
            activities.id,
            activities.name,
            activities.date,
            activities.time,
            activities.location,
            activities.description,
            activities.participants,

            COUNT(activity_participants.id) AS joined_count,

            CASE
                WHEN activity_participants_current.id IS NOT NULL
                THEN 1
                ELSE 0
            END AS joined

        FROM activities

        LEFT JOIN activity_participants
            ON activities.id = activity_participants.activity_id

        LEFT JOIN activity_participants AS activity_participants_current
            ON activities.id = activity_participants_current.activity_id
            AND activity_participants_current.user_id = ?

        GROUP BY activities.id

        ORDER BY activities.date ASC,
                 activities.time ASC
        """,
        (session["user_id"],)
    ).fetchall()

    connection.close()

    return render_template(
        "activities.html",
        activities=activities
    )


# =========================================================
# JOIN ACTIVITY
# =========================================================

@app.route("/join-activity/<int:activity_id>", methods=["POST"])
def join_activity(activity_id):

    if "user_id" not in session:

        return redirect(url_for("login"))

    connection = get_db_connection()

    activity = connection.execute(
        """
        SELECT
            activities.id,
            activities.participants,
            COUNT(activity_participants.id) AS joined_count

        FROM activities

        LEFT JOIN activity_participants
            ON activities.id = activity_participants.activity_id

        WHERE activities.id = ?

        GROUP BY activities.id
        """,
        (activity_id,)
    ).fetchone()

    if not activity:

        connection.close()

        return "Activity not found."

    existing = connection.execute(
        """
        SELECT id
        FROM activity_participants
        WHERE activity_id = ?
        AND user_id = ?
        """,
        (
            activity_id,
            session["user_id"]
        )
    ).fetchone()

    if existing:

        connection.close()

        return redirect(url_for("activities"))

    if activity["joined_count"] >= activity["participants"]:

        connection.close()

        return redirect(url_for("activities"))

    connection.execute(
        """
        INSERT INTO activity_participants
        (activity_id, user_id)
        VALUES (?, ?)
        """,
        (
            activity_id,
            session["user_id"]
        )
    )

    connection.commit()
    connection.close()

    return redirect(url_for("activities"))


# =========================================================
# LEAVE ACTIVITY
# =========================================================

@app.route("/leave-activity/<int:activity_id>", methods=["POST"])
def leave_activity(activity_id):

    if "user_id" not in session:

        return redirect(url_for("login"))

    connection = get_db_connection()

    connection.execute(
        """
        DELETE FROM activity_participants
        WHERE activity_id = ?
        AND user_id = ?
        """,
        (
            activity_id,
            session["user_id"]
        )
    )

    connection.commit()
    connection.close()

    return redirect(url_for("activities"))


# =========================================================
# SHELTER PROFILE
# =========================================================

@app.route("/shelter-profile")
def shelter_profile():

    if "shelter_id" not in session:

        return render_template(
            "shelter_login.html",
            message="Please log in as a shelter first."
        )

    connection = get_db_connection()

    shelter = connection.execute(
        """
        SELECT *
        FROM shelters
        WHERE id = ?
        """,
        (session["shelter_id"],)
    ).fetchone()

    connection.close()

    return render_template(
        "shelter_profile.html",
        shelter=shelter
    )


# =========================================================
# EDIT SHELTER PROFILE
# =========================================================

@app.route("/edit-shelter-profile", methods=["GET", "POST"])
def edit_shelter_profile():

    if "shelter_id" not in session:

        return render_template(
            "shelter_login.html",
            message="Please log in as a shelter first."
        )

    connection = get_db_connection()

    shelter = connection.execute(
        """
        SELECT *
        FROM shelters
        WHERE id = ?
        """,
        (session["shelter_id"],)
    ).fetchone()

    if request.method == "POST":

        shelter_name = request.form["shelter_name"]
        email = request.form["email"]
        phone = request.form["phone"]
        address = request.form["address"]

        connection.execute(
            """
            UPDATE shelters

            SET shelter_name = ?,
                email = ?,
                phone = ?,
                address = ?

            WHERE id = ?
            """,
            (
                shelter_name,
                email,
                phone,
                address,
                session["shelter_id"]
            )
        )

        connection.commit()
        connection.close()

        session["shelter_name"] = shelter_name

        return redirect(url_for("shelter_profile"))

    connection.close()

    return render_template(
        "edit_shelter_profile.html",
        shelter=shelter
    )


# =========================================================
# MY ACTIVITIES
# =========================================================

@app.route("/my-activities")
def my_activities():

    if "shelter_id" not in session:

        return render_template(
            "shelter_login.html",
            message="Please log in as a shelter first."
        )

    connection = get_db_connection()

    activities = connection.execute(
        """
        SELECT *
        FROM activities
        WHERE shelter_id = ?
        ORDER BY date ASC
        """,
        (session["shelter_id"],)
    ).fetchall()

    connection.close()

    return render_template(
        "my_activities.html",
        activities=activities
    )


# =========================================================
# VIEW ACTIVITY PARTICIPANTS
# =========================================================

@app.route("/activity-participants/<int:activity_id>")
def activity_participants(activity_id):

    if "shelter_id" not in session:

        return render_template(
            "shelter_login.html",
            message="Please log in as a shelter first."
        )

    connection = get_db_connection()

    activity = connection.execute(
        """
        SELECT *
        FROM activities
        WHERE id = ?
        AND shelter_id = ?
        """,
        (
            activity_id,
            session["shelter_id"]
        )
    ).fetchone()

    if not activity:

        connection.close()

        return "Activity not found."

    participants = connection.execute(
        """
        SELECT
            users.id,
            users.name,
            users.email

        FROM activity_participants

        JOIN users
            ON activity_participants.user_id = users.id

        WHERE activity_participants.activity_id = ?

        ORDER BY users.name ASC
        """,
        (activity_id,)
    ).fetchall()

    connection.close()

    return render_template(
        "activity_participants.html",
        activity=activity,
        participants=participants
    )


# =========================================================
# CREATE ACTIVITY
# =========================================================

@app.route("/create-activity", methods=["GET", "POST"])
def create_activity():

    if "shelter_id" not in session:

        return render_template(
            "shelter_login.html",
            message="Please log in as a shelter first."
        )

    if request.method == "POST":

        activity_name = request.form["activity_name"]
        activity_date = request.form["activity_date"]
        activity_time = request.form["activity_time"]
        location = request.form["location"]
        description = request.form["description"]
        participants = request.form["participants"]

        connection = get_db_connection()

        connection.execute(
            """
            INSERT INTO activities
            (
                shelter_id,
                name,
                date,
                time,
                location,
                description,
                participants
            )

            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session["shelter_id"],
                activity_name,
                activity_date,
                activity_time,
                location,
                description,
                participants
            )
        )

        connection.execute(
            """
            INSERT INTO notifications
            (shelter_id, message)

            VALUES (?, ?)
            """,
            (
                session["shelter_id"],
                "📅 Your activity '" + activity_name + "' was published successfully."
            )
        )

        connection.commit()
        connection.close()

        return render_template(
            "create_activity.html",
            message="Activity published successfully!"
        )

    return render_template("create_activity.html")


# =========================================================
# EDIT ACTIVITY
# =========================================================

@app.route("/edit-activity/<int:activity_id>", methods=["GET", "POST"])
def edit_activity(activity_id):

    if "shelter_id" not in session:

        return render_template(
            "shelter_login.html",
            message="Please log in as a shelter first."
        )

    connection = get_db_connection()

    activity = connection.execute(
        """
        SELECT *
        FROM activities

        WHERE id = ?
        AND shelter_id = ?
        """,
        (
            activity_id,
            session["shelter_id"]
        )
    ).fetchone()

    if not activity:

        connection.close()

        return render_template(
            "my_activities.html",
            activities=[],
            message="Activity not found."
        )

    if request.method == "POST":

        activity_name = request.form["activity_name"]
        activity_date = request.form["activity_date"]
        activity_time = request.form["activity_time"]
        location = request.form["location"]
        description = request.form["description"]
        participants = request.form["participants"]

        connection.execute(
            """
            UPDATE activities

            SET name = ?,
                date = ?,
                time = ?,
                location = ?,
                description = ?,
                participants = ?

            WHERE id = ?
            AND shelter_id = ?
            """,
            (
                activity_name,
                activity_date,
                activity_time,
                location,
                description,
                participants,
                activity_id,
                session["shelter_id"]
            )
        )

        connection.commit()
        connection.close()

        return redirect(url_for("my_activities"))

    connection.close()

    return render_template(
        "edit_activity.html",
        activity=activity
    )


# =========================================================
# DELETE ACTIVITY
# =========================================================

@app.route("/delete-activity/<int:activity_id>", methods=["POST"])
def delete_activity(activity_id):

    if "shelter_id" not in session:

        return render_template(
            "shelter_login.html",
            message="Please log in as a shelter first."
        )

    connection = get_db_connection()

    connection.execute(
        """
        DELETE FROM activity_participants
        WHERE activity_id = ?
        """,
        (activity_id,)
    )

    connection.execute(
        """
        DELETE FROM activities
        WHERE id = ?
        AND shelter_id = ?
        """,
        (
            activity_id,
            session["shelter_id"]
        )
    )

    connection.commit()
    connection.close()

    return redirect(url_for("my_activities"))


# =========================================================
# SHELTER COLLABORATIONS
# =========================================================

@app.route("/shelter-collaborations")
def shelter_collaborations():

    if "shelter_id" not in session:

        return render_template(
            "shelter_login.html",
            message="Please log in as a shelter first."
        )

    connection = get_db_connection()

    shelters = connection.execute(
        """
        SELECT
            id,
            shelter_name,
            email,
            phone,
            address

        FROM shelters

        ORDER BY shelter_name ASC
        """
    ).fetchall()

    connection.close()

    return render_template(
        "shelter_collaborations.html",
        shelters=shelters
    )


# =========================================================
# SHELTER DETAILS
# =========================================================

@app.route("/shelter/<int:shelter_id>")
def shelter_details(shelter_id):

    if "shelter_id" not in session:

        return render_template(
            "shelter_login.html",
            message="Please log in as a shelter first."
        )

    connection = get_db_connection()

    shelter = connection.execute(
        """
        SELECT
            id,
            shelter_name,
            email,
            phone,
            address

        FROM shelters

        WHERE id = ?
        """,
        (shelter_id,)
    ).fetchone()

    connection.close()

    if not shelter:

        return "Shelter not found."

    return render_template(
        "shelter_details.html",
        shelter=shelter
    )


# =========================================================
# NOTIFICATIONS
# =========================================================

@app.route("/notifications")
def notifications():

    # -----------------------------------------------------
    # ELDER NOTIFICATIONS
    # -----------------------------------------------------

    if "user_id" in session:

        connection = get_db_connection()

        user = connection.execute(
            """
            SELECT shelter_id
            FROM users
            WHERE id = ?
            """,
            (session["user_id"],)
        ).fetchone()

        if not user or not user["shelter_id"]:

            connection.close()

            return render_template(
                "notifications.html",
                notifications=[]
            )

        notifications = connection.execute(
            """
            SELECT *
            FROM notifications

            WHERE shelter_id = ?

            ORDER BY created_at DESC
            """,
            (user["shelter_id"],)
        ).fetchall()

        connection.close()

        return render_template(
            "notifications.html",
            notifications=notifications
        )

    # -----------------------------------------------------
    # SHELTER NOTIFICATIONS
    # -----------------------------------------------------

    if "shelter_id" in session:

        connection = get_db_connection()

        notifications = connection.execute(
            """
            SELECT *
            FROM notifications

            WHERE shelter_id = ?

            ORDER BY created_at DESC
            """,
            (session["shelter_id"],)
        ).fetchall()

        connection.close()

        return render_template(
            "notifications.html",
            notifications=notifications
        )

    # -----------------------------------------------------
    # NOT LOGGED IN
    # -----------------------------------------------------

    return redirect(url_for("login"))


# =========================================================
# SOS ALERT
# =========================================================

@app.route("/sos", methods=["GET", "POST"])
def sos():

    if "user_id" not in session:

        return redirect(url_for("login"))

    connection = get_db_connection()

    trusted_contact = connection.execute(
        """
        SELECT *
        FROM trusted_contacts

        WHERE user_id = ?

        ORDER BY name ASC

        LIMIT 1
        """,
        (session["user_id"],)
    ).fetchone()

    if request.method == "POST":

        message = request.form.get(
            "message",
            "I may need help. Please contact me as soon as possible."
        )

        location = request.form.get(
            "location",
            ""
        )

        alert_token = secrets.token_urlsafe(32)

        cursor = connection.execute(
            """
            INSERT INTO sos_alerts
            (
                user_id,
                message,
                location,
                alert_token
            )

            VALUES (?, ?, ?, ?)
            """,
            (
                session["user_id"],
                message,
                location,
                alert_token
            )
        )

        alert_id = cursor.lastrowid

        connection.commit()
        connection.close()

        alert_link = url_for(
            "view_sos_alert",
            token=alert_token,
            _external=True
        )

        return render_template(
            "sos_sent.html",
            trusted_contact=trusted_contact,
            message=message,
            location=location,
            alert_link=alert_link,
            alert_id=alert_id
        )

    connection.close()

    return render_template(
        "sos.html",
        trusted_contact=trusted_contact
    )


# =========================================================
# TRUSTED PERSON SOS ALERT
# =========================================================

@app.route("/sos-alert/<token>")
def view_sos_alert(token):

    connection = get_db_connection()

    alert = connection.execute(
        """
        SELECT
            sos_alerts.id,
            sos_alerts.message,
            sos_alerts.location,
            sos_alerts.created_at,
            users.name,
            users.email,
            users.phone

        FROM sos_alerts

        JOIN users
            ON sos_alerts.user_id = users.id

        WHERE sos_alerts.alert_token = ?
        """,
        (token,)
    ).fetchone()

    connection.close()

    if not alert:

        return "This SOS alert could not be found."

    return render_template(
        "trusted_sos_alert.html",
        alert=alert
    )


# =========================================================
# VIEW SOS ALERTS
# =========================================================

@app.route("/sos-alerts")
def sos_alerts():

    if "user_id" not in session:

        return redirect(url_for("login"))

    connection = get_db_connection()

    alerts = connection.execute(
        """
        SELECT
            sos_alerts.id,
            sos_alerts.message,
            sos_alerts.location,
            sos_alerts.created_at,
            users.name,
            users.email

        FROM sos_alerts

        JOIN users
            ON sos_alerts.user_id = users.id

        WHERE sos_alerts.user_id = ?

        ORDER BY sos_alerts.created_at DESC
        """,
        (session["user_id"],)
    ).fetchall()

    connection.close()

    return render_template(
        "sos_alerts.html",
        alerts=alerts
    )


# =========================================================
# SHELTER COMMUNITY
# =========================================================

@app.route("/shelter-community")
def shelter_community():

    if "shelter_id" not in session:

        return redirect(url_for("shelter_login"))

    connection = get_db_connection()

    posts = connection.execute(
        """
        SELECT
            community_posts.*,
            users.name AS user_name

        FROM community_posts

        LEFT JOIN users
            ON community_posts.user_id = users.id

        ORDER BY community_posts.created_at DESC
        """
    ).fetchall()

    comments = connection.execute(
        """
        SELECT
            post_comments.*,
            users.name AS user_name

        FROM post_comments

        LEFT JOIN users
            ON post_comments.user_id = users.id

        ORDER BY post_comments.created_at ASC
        """
    ).fetchall()

    connection.close()

    return render_template(
        "shelter_community.html",
        posts=posts,
        comments=comments
    )


# =========================================================
# SHELTER CONNECTION REQUESTS
# =========================================================

@app.route("/shelter-requests")
def shelter_requests():

    if "shelter_id" not in session:

        return redirect(url_for("shelter_login"))

    connection = get_db_connection()

    requests = connection.execute(
        """
        SELECT
            shelter_requests.id,
            shelter_requests.status,
            shelter_requests.created_at,
            users.name,
            users.email,
            users.phone,
            users.age,
            users.location

        FROM shelter_requests

        JOIN users
            ON shelter_requests.user_id = users.id

        WHERE shelter_requests.shelter_id = ?

        ORDER BY shelter_requests.created_at DESC
        """,
        (session["shelter_id"],)
    ).fetchall()

    connection.close()

    return render_template(
        "shelter_requests.html",
        requests=requests
    )


# =========================================================
# APPROVE SHELTER REQUEST
# =========================================================

@app.route("/approve-shelter-request/<int:request_id>", methods=["POST"])
def approve_shelter_request(request_id):

    if "shelter_id" not in session:

        return redirect(url_for("shelter_login"))

    connection = get_db_connection()

    connection_request = connection.execute(
        """
        SELECT *
        FROM shelter_requests

        WHERE id = ?
        AND shelter_id = ?
        """,
        (
            request_id,
            session["shelter_id"]
        )
    ).fetchone()

    if not connection_request:

        connection.close()

        return redirect(url_for("shelter_requests"))

    connection.execute(
        """
        UPDATE shelter_requests

        SET status = 'approved'

        WHERE id = ?
        """,
        (request_id,)
    )

    connection.execute(
        """
        UPDATE users

        SET
            shelter_id = ?,
            shelter_status = 'approved'

        WHERE id = ?
        """,
        (
            session["shelter_id"],
            connection_request["user_id"]
        )
    )

    connection.commit()
    connection.close()

    return redirect(url_for("shelter_requests"))


# =========================================================
# REJECT SHELTER REQUEST
# =========================================================

@app.route("/reject-shelter-request/<int:request_id>", methods=["POST"])
def reject_shelter_request(request_id):

    if "shelter_id" not in session:

        return redirect(url_for("shelter_login"))

    connection = get_db_connection()

    connection_request = connection.execute(
        """
        SELECT *
        FROM shelter_requests

        WHERE id = ?
        AND shelter_id = ?
        """,
        (
            request_id,
            session["shelter_id"]
        )
    ).fetchone()

    if not connection_request:

        connection.close()

        return redirect(url_for("shelter_requests"))

    connection.execute(
        """
        UPDATE shelter_requests

        SET status = 'rejected'

        WHERE id = ?
        """,
        (request_id,)
    )

    connection.execute(
        """
        UPDATE users

        SET
            shelter_id = NULL,
            shelter_status = 'rejected'

        WHERE id = ?
        """,
        (connection_request["user_id"],)
    )

    connection.commit()
    connection.close()

    return redirect(url_for("shelter_requests"))


# =========================================================
# START APPLICATION
# =========================================================

if __name__ == "__main__":

    create_tables()

    app.run(debug=True)