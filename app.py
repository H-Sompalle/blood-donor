# Import Libraries
from google.cloud import storage
import os
from cs50 import SQL
from flask import Flask, redirect, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from flask_session import Session
from helpers import apology
from re import fullmatch

# Initialize App
app = Flask(__name__)
db = SQL("sqlite:///blood_donor.db")
UPLOAD_FOLDER = '.'
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# Checks if file is allowed, i.e. whether its extension is correct
def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def upload_to_bucket(blob_name, path_to_file, bucket_name):
    """ Upload data to a bucket"""

    # Explicitly use service account credentials by specifying the private key
    # file.
    storage_client = storage.Client.from_service_account_json(
        'blood_bank.json')

    # print(buckets = list(storage_client.list_buckets())

    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.upload_from_filename(path_to_file)

    # returns a public url
    return blob.public_url


# Delete file
def delete_from_bucket(blob_name, bucket_name):
    """ Delete data from a bucket"""

    # Explicitly use service account credentials by specifying the private key
    # file.
    storage_client = storage.Client.from_service_account_json(
        'blood_bank.json')

    # print(buckets = list(storage_client.list_buckets())

    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.delete()


# Login Function
@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()
    if request.method == "GET":
        return render_template("login.html")
    else:
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", "/login", "Go back to login")
        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", "/login", "Go back to login")
        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", "/login", "Go back to login")
        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        # Redirect user to home page
        return redirect("/")


# Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# Register
@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    session.clear()
    if request.method == "POST":
        # Get the form details
        username = request.form.get("username")
        password = request.form.get("password")
        blood_type = request.form.get("blood_type")
        confirmation = request.form.get("confirmation")
        # See whether user exists
        rows_u = db.execute("SELECT * FROM users WHERE username = ?", username)
        if not username:
            return apology("Blank Username", "/register", "Go back to register")
        elif not password:
            return apology("Blank Password", "/register", "Go back to register")
        elif len(rows_u) != 0:
            return apology("Username Exists", "/register", "Go back to register")
        elif not confirmation:
            return apology("Blank Confirmation", "/register", "Go back to register")
        elif not blood_type:
            return apology("Please enter Blood Type", "/register", "Go back to register")
        elif password != confirmation:
            return apology("Password not matching confirmation", "/register", "Go back to register")
        else:
            db.execute("INSERT INTO users (username, hash, blood_type) VALUES(?, ?, ?)", username,
                       generate_password_hash(password), blood_type)
        return redirect("/login")
    else:
        # Render register.html
        return render_template("register.html", options=["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"])


# Index
@app.route("/")
def index():
    # Make the user login if not done
    if not session.get("user_id"):
        return redirect("/login")
    # Give the inputs and render index.html
    name = db.execute("SELECT username FROM users WHERE id=?", session["user_id"])
    p_list = db.execute("SELECT * FROM requests WHERE user_id = ? ORDER BY id DESC LIMIT 5", session["user_id"])
    return render_template("index.html", name=name[0]["username"], list=p_list)


# Add request
@app.route("/addrequest", methods=["GET", "POST"])
def addrequest():
    if request.method == "POST":
        blood_type = request.form.get("blood_type")
        location = request.form.get("location")
        regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email = request.form.get("email")
        country_code = request.form.get("countrycode")
        phone_number = request.form.get("phone")
        if not email:
            return apology("Please enter Email", "/addrequest", "Go back to Add a Request")
        if not fullmatch(regex, email):
            return apology("Please enter Valid Email", "/addrequest", "Go back to Add a Request")
        if not location:
            return apology("Please enter Location", "/addrequest", "Go back to Add a Request")
        if not country_code:
            return apology("Please enter Country Code", "/addrequest", "Go back to Add a Request")
        if len(phone_number) != 10 or int(phone_number) < 0:
            return apology("Invalid Phone", "/addrequest", "Go back to Add a Request")
        elif not blood_type:
            return apology("Please enter Blood Type", "/addrequest", "Go back to Add a Request")
        if 'file' not in request.files:
            return apology("Please submit a valid file", "/addrequest", "Go back to Add a Request")
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            return apology("Please submit a valid file", "/addrequest", "Go back to Add a Request")
        if file and allowed_file(file.filename):
            pass
        else:
            return apology("Please submit a valid file (PDFs only) ", "/addrequest", "Go back to Add a Request")
        result_id = db.execute("INSERT INTO requests (user_id, blood_type, location, email, phone_number, matched, country_code) VALUES(?, ?, ?, ?, ?, ?, ?)",session["user_id"], blood_type, location, email, phone_number, "false", country_code)
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        x = upload_to_bucket(str(result_id) + ".pdf", os.path.join(app.config['UPLOAD_FOLDER'], filename), "blood-donor")
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        db.execute("UPDATE requests SET prescription = ? WHERE id=?", x, result_id)
        db.execute(
            "INSERT INTO history (type, blood_type, location, email, phone_number, matched, request_id, user_id) VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
            "Add request", blood_type, location, email, phone_number, "false", result_id, session["user_id"])
        return redirect("/")
    else:
        return render_template("addrequest.html", options=["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"], options_phone=['Afghanistan (93)',
'Albania (355)',
'Algeria (213)',
'American Samoa (1-684)',
'Andorra (376)',
'Angola (244)',
'Anguilla (1-264)',
'Antarctica (672)',
'Antigua and Barbuda (1-268)',
'Argentina (54)',
'Armenia (374)',
'Aruba (297)',
'Australia (61)',
'Austria (43)',
'Azerbaijan (994)',
'Bahamas (1-242)',
'Bahrain (973)',
'Bangladesh (880)',
'Barbados (1-246)',
'Belarus (375)',
'Belgium (32)',
'Belize (501)',
'Benin (229)',
'Bermuda (1-441)',
'Bhutan (975)',
'Bolivia (591)',
'Bosnia and Herzegovina (387)',
'Botswana (267)',
'Brazil (55)',
'British Indian Ocean Territory (246)',
'British Virgin Islands (1-284)',
'Brunei (673)',
'Bulgaria (359)',
'Burkina Faso (226)',
'Burundi (257)',
'Cambodia (855)',
'Cameroon (237)',
'Canada (1)',
'Cape Verde (238)',
'Cayman Islands (1-345)',
'Central African Republic (236)',
'Chad (235)',
'Chile (56)',
'China (86)',
'Christmas Island (61)',
'Cocos Islands (61)',
'Colombia (57)',
'Comoros (269)',
'Cook Islands (682)',
'Costa Rica (506)',
'Croatia (385)',
'Cuba (53)',
'Curacao (599)',
'Cyprus (357)',
'Czech Republic (420)',
'Democratic Republic of the Congo (243)',
'Denmark (45)',
'Djibouti (253)',
'Dominica (1-767)',
'Dominican Republic (1-809, 1-829, 1-849)',
'East Timor (670)',
'Ecuador (593)',
'Egypt (20)',
'El Salvador (503)',
'Equatorial Guinea (240)',
'Eritrea (291)',
'Estonia (372)',
'Ethiopia (251)',
'Falkland Islands (500)',
'Faroe Islands (298)',
'Fiji (679)',
'Finland (358)',
'France (33)',
'French Polynesia (689)',
'Gabon (241)',
'Gambia (220)',
'Georgia (995)',
'Germany (49)',
'Ghana (233)',
'Gibraltar (350)',
'Greece (30)',
'Greenland (299)',
'Grenada (1-473)',
'Guam (1-671)',
'Guatemala (502)',
'Guernsey (44-1481)',
'Guinea (224)',
'Guinea-Bissau (245)',
'Guyana (592)',
'Haiti (509)',
'Honduras (504)',
'Hong Kong (852)',
'Hungary (36)',
'Iceland (354)',
'India (91)',
'Indonesia (62)',
'Iran (98)',
'Iraq (964)',
'Ireland (353)',
'Isle of Man (44-1624)',
'Israel (972)',
'Italy (39)',
'Ivory Coast (225)',
'Jamaica (1-876)',
'Japan (81)',
'Jersey (44-1534)',
'Jordan (962)',
'Kazakhstan (7)',
'Kenya (254)',
'Kiribati (686)',
'Kosovo (383)',
'Kuwait (965)',
'Kyrgyzstan (996)',
'Laos (856)',
'Latvia (371)',
'Lebanon (961)',
'Lesotho (266)',
'Liberia (231)',
'Libya (218)',
'Liechtenstein (423)',
'Lithuania (370)',
'Luxembourg (352)',
'Macau (853)',
'Macedonia (389)',
'Madagascar (261)',
'Malawi (265)',
'Malaysia (60)',
'Maldives (960)',
'Mali (223)',
'Malta (356)',
'Marshall Islands (692)',
'Mauritania (222)',
'Mauritius (230)',
'Mayotte (262)',
'Mexico (52)',
'Micronesia (691)',
'Moldova (373)',
'Monaco (377)',
'Mongolia (976)',
'Montenegro (382)',
'Montserrat (1-664)',
'Morocco (212)',
'Mozambique (258)',
'Myanmar (95)',
'Namibia (264)',
'Nauru (674)',
'Nepal (977)',
'Netherlands (31)',
'Netherlands Antilles (599)',
'New Caledonia (687)',
'New Zealand (64)',
'Nicaragua (505)',
'Niger (227)',
'Nigeria (234)',
'Niue (683)',
'North Korea (850)',
'Northern Mariana Islands (1-670)',
'Norway (47)',
'Oman (968)',
'Pakistan (92)',
'Palau (680)',
'Palestine (970)',
'Panama (507)',
'Papua New Guinea (675)',
'Paraguay (595)',
'Peru (51)',
'Philippines (63)',
'Pitcairn (64)',
'Poland (48)',
'Portugal (351)',
'Puerto Rico (1-787, 1-939)',
'Qatar (974)',
'Republic of the Congo (242)',
'Reunion (262)',
'Romania (40)',
'Russia (7)',
'Rwanda (250)',
'Saint Barthelemy (590)',
'Saint Helena (290)',
'Saint Kitts and Nevis (1-869)',
'Saint Lucia (1-758)',
'Saint Martin (590)',
'Saint Pierre and Miquelon (508)',
'Saint Vincent and the Grenadines (1-784)',
'Samoa (685)',
'San Marino (378)',
'Sao Tome and Principe (239)',
'Saudi Arabia (966)',
'Senegal (221)',
'Serbia (381)',
'Seychelles (248)',
'Sierra Leone (232)',
'Singapore (65)',
'Sint Maarten (1-721)',
'Slovakia (421)',
'Slovenia (386)',
'Solomon Islands (677)',
'Somalia (252)',
'South Africa (27)',
'South Korea (82)',
'South Sudan (211)',
'Spain (34)',
'Sri Lanka (94)',
'Sudan (249)',
'Suriname (597)',
'Svalbard and Jan Mayen (47)',
'Swaziland (268)',
'Sweden (46)',
'Switzerland (41)',
'Syria (963)',
'Taiwan (886)',
'Tajikistan (992)',
'Tanzania (255)',
'Thailand (66)',
'Togo (228)',
'Tokelau (690)',
'Tonga (676)',
'Trinidad and Tobago (1-868)',
'Tunisia (216)',
'Turkey (90)',
'Turkmenistan (993)',
'Turks and Caicos Islands (1-649)',
'Tuvalu (688)',
'U.S. Virgin Islands (1-340)',
'Uganda (256)',
'Ukraine (380)',
'United Arab Emirates (971)',
'United Kingdom (44)',
'United States (1)',
'Uruguay (598)',
'Uzbekistan (998)',
'Vanuatu (678)',
'Vatican (379)',
'Venezuela (58)',
'Vietnam (84)',
'Wallis and Futuna (681)',
'Western Sahara (212)',
'Yemen (967)',
'Zambia (260)',
'Zimbabwe (263)'])


# Requests
@app.route("/requests", methods=["GET", "POST"])
def requests():
    if request.method == "POST":
        location = request.form.get("location")
        blood_type = request.form.get("blood_type")
        if not location:
            return apology("Please enter Location", "/requests", "Go back to requests")
        if not blood_type:
            return apology("Please enter Blood Type", "/requests", "Go back to requests")
        p_list = db.execute("SELECT * FROM requests WHERE blood_type=? AND location=? AND matched=? AND NOT user_id=?", blood_type, location, 'false', session["user_id"])
        return render_template("requests.html", message="Requests where location is " + location + ", and blood type is " + blood_type, list=p_list)
    else:
        return render_template("filter.html", options=["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"])


# My Requests
@app.route("/myrequests", methods=["GET", "POST"])
def myrequests():
    if request.method == "POST":
        location = request.form.get("location")
        blood_type = request.form.get("blood_type")
        if not location:
            return apology("Please enter Location", "/requests", "Go back to requests")
        if not blood_type:
            return apology("Please enter Blood Type", "/requests", "Go back to requests")
        p_list = db.execute("SELECT * FROM requests WHERE blood_type=? AND location=? AND user_id=?", blood_type, location, session["user_id"])
        return render_template("myrequests.html", message="My Requests where location is " + location + ", and blood type is " + blood_type, list=p_list)
    else:
        return render_template("mfilter.html", options=["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"])


# Fulfillment of Request
@app.route("/fulfil", methods=["POST", "GET"])
def fulfil():
    if request.method == "POST":
        p_fulfil = request.form.get("fulfil")
        m = db.execute("SELECT user_id FROM requests WHERE id = ?", p_fulfil)
        print(len(m))
        if len(m) == 0:
            return apology("Invalid Number", "/fulfil", "Go back to Fulfilling a Request")
        if m[0]["user_id"] == session["user_id"]:
            db.execute("DELETE FROM requests WHERE id = ?", p_fulfil)
            db.execute(
                "INSERT INTO history (type, blood_type, location, email, phone_number, matched, request_id, user_id) VALUES(?, "
                "?, ?, ?, ?, ?, ?, ?)",
                "Fulfil request", "N/A", "N/A", "N/A", "N/A", "false", p_fulfil, session["user_id"])
        else:
            return apology("You can't fulfil a request that isn't yours", "/fulfil", "Go back to Fulfilling a Request")
        return redirect("/")
    else:
        return render_template("fulfil.html")


# History
@app.route("/history")
def history():
    p_list = db.execute("SELECT * FROM history WHERE user_id=?", session["user_id"])
    return render_template("history.html", message="History", list=p_list)


# Terms
@app.route("/terms")
def terms():
    return render_template("terms.html")


# Match
@app.route("/match", methods=["POST", "GET"])
def match():
    if request.method == "POST":
        p_match = request.form.get("match")
        m = db.execute("SELECT user_id FROM requests WHERE id = ?", p_match)
        if len(m) == 0:
            return apology("Invalid Number", "/match", "Go back to Matching a Request")
        if m[0]["user_id"] == session["user_id"]:
            delete_from_bucket(str(p_match) + ".pdf", "blood-donor")
            db.execute("UPDATE requests SET matched=?, prescription=? WHERE id = ?", 'true', 'N/A', p_match)
            db.execute(
                "INSERT INTO history (type, blood_type, location, email, phone_number, matched, request_id, user_id) VALUES(?, "
                "?, ?, ?, ?, ?, ?, ?)",
                "Match request", "N/A", "N/A", "N/A", "N/A", "false", p_match, session["user_id"])
        else:
            return apology("You can't match a request that isn't yours", "/match", "Go back to Matching a Request")
        return redirect("/")
    else:
        return render_template("match.html", options=["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"])
