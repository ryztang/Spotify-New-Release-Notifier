import sqlite3
from sqlite3 import Error

import os.path

import json

with open("config.json") as config_file:
    config = json.load(config_file)

# Local SQLite database storing new release data obtained from Spotify API
SQLITE_PATH = config["new_release_db_path"]

# Local SQLite database storing extra application configuration
CONFIG_DB_PATH = config["config_db_path"]

CREATE_ALBUMS_TABLE = "CREATE TABLE Albums (" \
                      "AlbumID TEXT PRIMARY KEY, " \
                      "CollectionDate TEXT, " \
                      "Name TEXT, " \
                      "ReleaseDate TEXT, " \
                      "ImageURL TEXT" \
                      ");"

CREATE_TRACKS_TABLE = "CREATE TABLE Tracks (" \
                      "TrackID TEXT PRIMARY KEY, " \
                      "SingleCollectionDate TEXT, " \
                      "Name TEXT, " \
                      "PreviewURL TEXT, " \
                      "SingleTrackNumber INTEGER, " \
                      "SingleReleaseDate TEXT, " \
                      "SingleImageURL TEXT" \
                      ");"

CREATE_ARTISTS_TABLE = "CREATE TABLE Artists (" \
                       "ArtistID TEXT PRIMARY KEY, " \
                       "Name TEXT, " \
                       "Popularity INTEGER" \
                       ");"

CREATE_ARTIST_GENRE_TABLE = "CREATE TABLE Artist_Genre (" \
                            "ArtistID TEXT, " \
                            "Genre TEXT, " \
                            "PRIMARY KEY (ArtistID, Genre), " \
                            "FOREIGN KEY (ArtistID) REFERENCES Artists(ArtistID)" \
                            ");"

CREATE_ALBUM_ARTIST_TABLE = "CREATE TABLE Album_Artist (" \
                            "AlbumID TEXT, " \
                            "ArtistID TEXT, " \
                            "PRIMARY KEY (AlbumID, ArtistID), " \
                            "FOREIGN KEY (AlbumID) REFERENCES Albums(AlbumID), " \
                            "FOREIGN KEY (ArtistID) REFERENCES Artists(ArtistID)" \
                            ");"

CREATE_ALBUM_TRACK_TABLE = "CREATE TABLE Album_Track (" \
                           "AlbumID TEXT, " \
                           "TrackID TEXT, " \
                           "TrackNumber INTEGER, " \
                           "PRIMARY KEY (AlbumID, TrackID), " \
                           "FOREIGN KEY (AlbumID) REFERENCES Albums(AlbumID), " \
                           "FOREIGN KEY (TrackID) REFERENCES Tracks(TrackID)" \
                           ");"

CREATE_TRACK_ARTIST_TABLE = "CREATE TABLE Track_Artist (" \
                            "TrackID TEXT, " \
                            "ArtistID TEXT, " \
                            "PRIMARY KEY (TrackID, ArtistID), " \
                            "FOREIGN KEY (TrackID) REFERENCES Tracks(TrackID), " \
                            "FOREIGN KEY (ArtistID) REFERENCES Artists(ArtistID)" \
                            ");"


# Connect to a SQLite database
def _connect(db_file):
    try:
        conn = sqlite3.connect(db_file)
        print("Connected to SQLite\n")
        return conn
    except Error as e:
        print(e)


# Create a table with the given SQLite conn
def create_table(conn, create_table_sql):
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)


# Connect to local database storing new release data, creating file and database design if it doesn't already exist
def create_sqlite_connection():
    if os.path.isfile(SQLITE_PATH):
        print("SQLite file exists")
        conn = _connect(SQLITE_PATH)
    else:
        print("SQLite file created")
        conn = _connect(SQLITE_PATH)
        create_table(conn, CREATE_ALBUMS_TABLE)
        create_table(conn, CREATE_TRACKS_TABLE)
        create_table(conn, CREATE_ARTISTS_TABLE)
        create_table(conn, CREATE_ARTIST_GENRE_TABLE)
        create_table(conn, CREATE_ALBUM_ARTIST_TABLE)
        create_table(conn, CREATE_ALBUM_TRACK_TABLE)
        create_table(conn, CREATE_TRACK_ARTIST_TABLE)
    return conn


# Connect to local configuration database (this must already exist; the application doesn't create it)
def create_config_connection():
    if os.path.isfile(CONFIG_DB_PATH):
        print("Config database exists")
        conn = _connect(CONFIG_DB_PATH)
    else:
        raise Exception("Config database doesn't exist")
    return conn
