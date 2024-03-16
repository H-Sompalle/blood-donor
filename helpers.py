import requests
from flask import render_template


# Apology Function
def apology(message, link, redirect_message):
    return render_template("apology.html", message=message, link=link, redirect_text=redirect_message)
