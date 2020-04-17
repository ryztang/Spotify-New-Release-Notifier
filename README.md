# Spotify-New-Release-Notifier
Spotify New Release Notifier is a Python application that sends email notifications listing new album and single track releases, sorted by artist popularity, to registered recipients. 
Artist and genre details are included for each new release and recipients can play snippets of new tracks.

There are two steps to this application when it is run.
  
First, new release data is collected from the Spotify API and stored into a local SQLite database (see New_Release_DB_Design.PNG for details on the database design). This is handled by api_client.py using pandas and the Python library for the Spotify Web API, Spotipy. Album and single track data are only added to the database if they haven't already been added. This prevents the same data from being sent in subsequent email notifications.
  
Next, the most recent albums and singles collected are included in the email notification to be sent. This is handled by email_notifier.py. It sends emails to the recipients specified in the local configuration database (see Config_DB_Design.PNG for details regarding how recipient data is stored). If there are no new releases, no email is sent.

### Data Flow Diagram:
![Data Flow Diagram](Data_Flow_Diagram.PNG?raw=true)
  
### Email Sample Screenshot:
![Email Screenshot](Email_Sample_Screenshot.PNG?raw=true)
  
### New Release DB Diagram:
![New Release DB Diagram](New_Release_DB_Design.PNG?raw=true)

## Setup
1. Clone this repository.
  
2. Install either Miniconda or Anaconda (Miniconda would suffice since pandas is the only package used).  
   You can find Miniconda installers here: https://docs.conda.io/en/latest/miniconda.html#
   
3. Install SQLite.
   You can do so here: https://www.sqlite.org/download.html
  
3. Enter the full path to Miniconda or Anaconda to the respective commands in setup.bat and main.bat.
  
4. Run setup.bat. This opens Anaconda Prompt to create a new conda environment for this project and install the necessary libraries.
  
5. In order to run this notifier, this application must be registered under a Spotify account. 
   To do this, head to the Spotify for Developers Dashboard (https://developer.spotify.com/dashboard/) and create a new application under your account.  
   Once the new Client ID and Client Secret are obtained, enter them into their respective positions in config.json, along with your Spotify username (this can be found under Account Overview when you're logged into Spotify).
  
6. Choose a redirect uri and enter it into config.json. Also, add the redirect uri to the application on the Spotify Dashboard (click Edit Settings).
The app will append the authentication code to this uri the first time it is run (it is recommended that you use "http://localhost/"). 
   
7. Enter the preferred sender email address and password to config.json. 
It is recommended that you create a new email for this as you must also update its settings to allow apps to access it.
  
8. Enter the SMTP server to config.json (e.g. "smtp.gmail.com" for Gmail).
  
9. When the application is run, it will create a local SQLite database to store records of data collected from the Spotify API.
The location of this database must be specified in config.json, including the file name with a .sqlite or .db extension 
(e.g. "C:/Spotify_DBs/SpotifyNewReleaseDatabase.sqlite").
  
10. The application also connects to a local configuration database which stores a list of recipients of the email notifications.
This config database must already exist before the application is run. 
See Config_DB_Design.PNG to see how this database is expected to be designed and create it (it is only one table with two columns).
Then, enter the full path to that database into config.json (e.g. "C:/Spotify_DBs/config.sqlite").

## Running the Application
To run this application, simply run main.bat. 
This expects the app to be fully configured, so make sure to follow and fully complete the setup before running.  
main.bat opens Anaconda Prompt, activates the environment created by setup.bat, and runs main.py, which would then send email notifications to everyone saved in the configuration database.
  
The first time you run this application, Spotify will ask you to authorize the app, after which it will redirect you to the configured redirect uri with an authorization code appended.
Enter this entire url when prompted by the application (which would be displayed on the console). 
After it receives the authorization code, the app will obtain a token to access the Spotify API endpoints.
You will only have to do this once as the token is cached for future use and automatically refreshed upon expiration.
  
If you wish to run this application regularly, you can add it to Windows Task Scheduler or another scheduling program.
Also, this app is configured by default to obtain only the 10 newest releases at a time. This can be changed in config.json.

## Possible Enhancements
1. An improved front-end for the email:  
Currently, the html layout of the email is not very responsive, especially on mobile. Many improvements can be made so that the UI looks smoother.
  
2. Webpage to update the config database:  
Currently, the configuration database must be updated directly using SQL. 
In the future, it would be ideal to have a website that could manage who subscribes to these notifications and update the config database accordingly.

3. More specific configuration for each recipient:  
Currently, one email is sent to all recipients, so each recipient receives the same content.
A possible enhancement would be to configure the application so that it sends a specific email to each recipient depending on their wants/interests.
  
## Additional Notes
This application uses Spotipy, which is an open-source Python library that eases access to the Spotify Web API.  
Documentation can be found here: https://spotipy.readthedocs.io/en/2.11.1/  
GitHub repository can be found here: https://github.com/plamere/spotipy
