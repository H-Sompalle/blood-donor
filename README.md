# Blood Donor
#### Video Demo: https://youtu.be/MeJmAiVGJL8
#### Motivation
Every day 12,000 people in India die due to the sheer lack of donated blood. India collects 11 million units of blood but needs 15 million units, so there’s a deficit of 4 million units. Seeing these shocking statistics, I decided to create Blood Donor to make it easier for donating and recieving blood.
#### Brief Summary of the Project
This web app helps in requesting for blood. Users can request for blood and other users can see the request details and the contact email and phone number to reach out to the requester. Users can then match their requests once somebody has agrred to donate, then fulfil it once it is done.
#### The Application
Here is the application flow for requesters:
  
1. You register on the website by giving your username, password and blood type
2. You are redirected to the login page where you login with your username and password
3. You then are taken to your dashboard, which shows the 5 most recent donations are shown 
4. You can then request for blood by filling in the blood type, location, email, phone number, and upload the doctor's prescription
5. After that, if somebody has contacted you, you can match the request in order to make sure that people don't mistake your request for a pending request
6. Finally you fulfil that request if the donation is over
  
Here is the application flow for donators:
  
1. Go to requests
2. See the location, blood type, phone number, email
3. Contact the requester
4. Go to the hospital and donate
  
#### The Implementation
The main components of this application was:
  
1. Flask
2. Google Cloud Storage
  
First, I created app.py. Then I created flask templates. Each of the templates were taken from a starter template of layout.html.
Then, I developed each of them one by one. One of the common elements seen across the pages was the menu bar which was created with inspiration from CS50 Finance and a some customization.
The other important element was the location field where I used an API to retrieve auto-complete suggestions from Google Cloud.
After that, I created my own apology function which gives an apology with customized logos.
I got the inspiration from the apology function in CS50 Finance, but decided to create a generic apology instead of using memes.
The database that I used was SQLite.
I had 3 tables.
  
1. Users
2. Requests
3. History
  
The users table contaisd the usernames, hashes, and blood types.
The requests table contains the location, user_id, email, phone number match, and blood type.
The history table contains type of operation and the required parameters.
#### Conclusion
This was a great experience for me.
Building such a project for one of the most noble causes is one of the best things I could ever do.
I hope that my app will help people recieve and donate blood faster and easier.
#### Citations
###### File Upload
https://flask.palletsprojects.com/en/2.2.x/patterns/fileuploads/
https://stackoverflow.com/questions/37003862/how-to-upload-a-file-to-google-cloud-storage-on-python-3
###### Menu Bar
https://www.w3schools.com/bootstrap4/tryit.asp?filename=trybs_navbar_color&stacked=h
https://finance.cs50.net/login
###### Google Maps Autocomplete
https://www.youtube.com/watch?v=c3MjU9E9buQ&t=191s
###### Email Checking
https://www.geeksforgeeks.org/check-if-email-address-valid-or-not-in-python/
###### Hashing and Apology
CS50 Finance Problem Set
