import pandas as pd

import sql_utils

from datetime import datetime

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import json


# EmailNotifier handles the sending of email notifications to recipients
class EmailNotifier:

    PORT = 465

    def __init__(self):

        # Connect to local database storing new release data
        self.conn = sql_utils.create_sqlite_connection()

        # Connect to local configuration database
        config_conn = sql_utils.create_config_connection()

        # Obtain recipients from configuration database
        self.recipients_df = pd.read_sql("SELECT EmailAddress, Name FROM Notification_Recipients", config_conn)

        self.html = None
        self.new_albums = True
        self.new_singles = True
        self.albums_df = None
        self.album_tracks_df = None
        self.single_tracks_df = None

        with open("config.json") as config_file:
            config = json.load(config_file)

        # Obtain info for the sender email from config.json
        self.email = config["sender_email"]
        self.password = config["sender_password"]
        self.smtpserver = config["smtp_server"]

    def __del__(self):
        self.conn.close()

    # Gets up-to-date data from local database storing new release data to send in email notification
    def get_data_to_send(self):

        # Store albums into a dataframe
        self.albums_df = pd.read_sql("SELECT Albums.AlbumID AS AlbumID, Albums.Name AS Album_Name, ReleaseDate, " +
                                     "ImageURL, Artists.ArtistID AS ArtistID, Artists.Name AS Artist_Name, " +
                                     "Popularity " +
                                     "FROM Albums " +
                                     "INNER JOIN Album_Artist ON Albums.AlbumID = Album_Artist.AlbumID " +
                                     "INNER JOIN Artists ON Album_Artist.ArtistID = Artists.ArtistID " +
                                     "WHERE CollectionDate = '" +
                                     datetime.today().strftime("%Y-%m-%d") + "' " +
                                     "ORDER BY Popularity DESC", self.conn)

        if self.albums_df.empty:
            self.new_albums = False

        # Store tracks in albums into a dataframe
        self.album_tracks_df = pd.read_sql(
            "SELECT Album_Track.AlbumID AS AlbumID, Album_Track.TrackID AS TrackID, " +
            "Album_Track.TrackNumber AS TrackNumber, Tracks.Name AS Track_Name, PreviewURL, " +
            "Artists.Name AS Artist_Name " +
            "FROM Albums " +
            "INNER JOIN Album_Track ON Albums.AlbumID = Album_Track.AlbumID " +
            "INNER JOIN Tracks ON Album_Track.TrackID = Tracks.TrackID " +
            "INNER JOIN Track_Artist ON Tracks.TrackID = Track_Artist.TrackID " +
            "INNER JOIN Artists ON Track_Artist.ArtistID = Artists.ArtistID " +
            "WHERE Albums.CollectionDate = '" +
            datetime.today().strftime("%Y-%m-%d") + "'", self.conn)

        # Store singles into a dataframe
        self.single_tracks_df = pd.read_sql(
            "SELECT Tracks.TrackID AS TrackID, Tracks.Name AS Track_Name, PreviewURL, SingleReleaseDate, " +
            "SingleImageURL, Artists.ArtistID AS ArtistID, Artists.Name AS Artist_Name, Popularity " +
            "FROM Tracks " +
            "INNER JOIN Track_Artist ON Tracks.TrackID = Track_Artist.TrackID " +
            "INNER JOIN Artists ON Artists.ArtistID = Track_Artist.ArtistID " +
            "WHERE SingleCollectionDate = '" +
            datetime.today().strftime("%Y-%m-%d") + "' " +
            "ORDER BY Popularity DESC", self.conn)

        if self.single_tracks_df.empty:
            self.new_singles = False

        if not self.new_albums and not self.new_singles:
            return False

        return True

    # Add new albums to html of email
    def _add_albums(self):
        encountered_albums = []
        for index, row in self.albums_df.iterrows():

            album_id = row["AlbumID"]
            if album_id in encountered_albums:
                continue

            album_name = row["Album_Name"]
            release_date = row["ReleaseDate"]
            image_url = row["ImageURL"]
            needed_albums = self.albums_df.loc[self.albums_df["AlbumID"] == album_id]
            album_artists = []
            album_artist_ids = []
            for i, artist_row in needed_albums.iterrows():
                album_artist_ids.append(artist_row["ArtistID"])
                album_artists.append(artist_row["Artist_Name"])

            self.html = self.html + "<table style='margin-bottom:25px'><tr>"

            self.html = self.html + "<td valign='top'><img src=" + \
                image_url + \
                " style='width:300px;height:300px;'></td>"

            self.html = self.html + "<td valign='top'><h2 style='line-height:15px;margin-left:40px;'>" + \
                album_name + \
                "</h2>"

            # Add album artists to html of email
            self.html = self.html + "<h3 style='margin-left:40px;'>by " + album_artists[0]
            for i in range(1, len(album_artists)):
                self.html = self.html + ", " + album_artists[i]
            self.html = self.html + "</h3>"

            tracks_in_album = self.album_tracks_df.loc[self.album_tracks_df["AlbumID"] == album_id]
            tracks_in_album.sort_values(by=["TrackNumber"])

            # Add album's tracks to html of email
            encountered_tracks = []
            for track_index, track_row in tracks_in_album.iterrows():
                track_id = track_row["TrackID"]
                if track_id in encountered_tracks:
                    continue
                track_name = track_row["Track_Name"]
                track_number = track_row["TrackNumber"]
                track_preview = track_row["PreviewURL"]
                needed_tracks = tracks_in_album.loc[tracks_in_album["TrackID"] == track_id]
                track_artists = []
                for i, artist_row in needed_tracks.iterrows():
                    track_artists.append(artist_row["Artist_Name"])

                for artist in album_artists:
                    track_artists.remove(artist)

                self.html = self.html + "<h4 style='margin-left:80px;'>" + str(track_number) + ". "

                if track_preview:
                    self.html = self.html + "<a href='" + track_preview + "'>"

                self.html = self.html + track_name

                if track_preview:
                    self.html = self.html + "</a>"

                if track_artists:
                    self.html = self.html + " ft. " + track_artists[0]
                    for i in range(1, len(track_artists)):
                        self.html = self.html + ", " + track_artists[i]
                self.html = self.html + "</h4>"

                encountered_tracks.append(track_id)

            # Add album genres to html of email
            genres = []
            for artist_id in album_artist_ids:
                artist_genres = pd.read_sql("SELECT Genre FROM Artist_Genre WHERE ArtistID = '" + artist_id + "'",
                                            self.conn)
                for i, genre_row in artist_genres.iterrows():
                    genres.append(genre_row["Genre"])

            genres = list(dict.fromkeys(genres))

            if genres:
                self.html = self.html + "<h3 style='margin-left:40px;'>Genres: " + genres[0]
                for i in range(1, len(genres)):
                    self.html = self.html + ", " + genres[i]
                self.html = self.html + "</h3>"

            # Add album release date to html of email
            self.html = self.html + "<h3 style='margin-left:40px;'>Released: " + release_date + "</h3></td>"

            self.html = self.html + "</tr></table>"

            encountered_albums.append(album_id)

    # Add new singles to html of email
    def _add_singles(self):
        encountered_singles = []
        for index, row in self.single_tracks_df.iterrows():

            track_id = row["TrackID"]
            if track_id in encountered_singles:
                continue

            track_name = row["Track_Name"]
            track_preview = row["PreviewURL"]
            track_release_date = row["SingleReleaseDate"]
            track_image = row["SingleImageURL"]
            needed_singles = self.single_tracks_df.loc[self.single_tracks_df["TrackID"] == track_id]
            single_artists = []
            single_artist_ids = []
            for i, artist_row in needed_singles.iterrows():
                single_artist_ids.append(artist_row["ArtistID"])
                single_artists.append(artist_row["Artist_Name"])

            self.html = self.html + "<table style='margin-bottom:25px'><tr>"

            self.html = self.html + "<td valign='top'><img src=" + track_image + \
                " style='width:200px;height:200px;'></td>"

            self.html = self.html + "<td valign='top'><h2 style='line-height:15px;margin-left:40px;'>"

            if track_preview:
                self.html = self.html + "<a href='" + track_preview + "'>"

            self.html = self.html + track_name

            if track_preview:
                self.html = self.html + "</a>"

            self.html = self.html + "</h2>"

            # Add single artists to html of email
            self.html = self.html + "<h3 style='margin-left:40px;'>by " + single_artists[0]
            for i in range(1, len(single_artists)):
                self.html = self.html + ", " + single_artists[i]
            self.html = self.html + "</h3>"

            # Add genres of single to html of email
            genres = []
            for artist_id in single_artist_ids:
                artist_genres = pd.read_sql("SELECT Genre FROM Artist_Genre WHERE ArtistID = '" + artist_id + "'",
                                            self.conn)
                for i, genre_row in artist_genres.iterrows():
                    genres.append(genre_row["Genre"])

            genres = list(dict.fromkeys(genres))

            if genres:
                self.html = self.html + "<h3 style='margin-left:40px;'>Genres: " + genres[0]
                for i in range(1, len(genres)):
                    self.html = self.html + ", " + genres[i]
                self.html = self.html + "</h3>"

            # Add single release date to html of email
            self.html = self.html + "<h3 style='margin-left:40px;'>Released: " + track_release_date + "</h3></td>"

            self.html = self.html + "</tr></table>"

            encountered_singles.append(track_id)

    # Construct html of email to send
    def _construct_email(self):
        self.html = """\
            <html>
              <head>
              </head>
              <body>
                <h1>New Releases on Spotify</h1>
            """

        # Construct albums part of email
        if self.new_albums:
            self.html = self.html + "<h2 style='margin-bottom:25px;'><u>Albums</u></h2>"

        self._add_albums()

        # Construct singles part of email
        if self.new_singles:
            self.html = self.html + "<h2 style='margin-bottom:25px;'><u>Singles</u></h2>"

        self._add_singles()

        self.html = self.html + """
              </body>
            </html>
            """

    # Send email notification to recipients
    def send_email(self):
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(self.smtpserver, self.PORT, context=context) as server:

            recipients = []
            for index, row in self.recipients_df.iterrows():
                recipients.append(row["EmailAddress"])

            message = MIMEMultipart("alternative")
            message["Subject"] = "Spotify New Releases"
            message["From"] = self.email

            # Keep recipient emails hidden from other recipients
            message["To"] = self.email

            self._construct_email()

            htmlpart = MIMEText(self.html, "html")
            message.attach(htmlpart)

            server.login(self.email, self.password)
            server.sendmail(self.email, [self.email] + recipients, message.as_string())
