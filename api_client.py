import spotipy
import spotipy.util as util

import sql_utils

import pandas as pd

from datetime import datetime

import json


# APIClient handles collection of data from Spotify API into a local database
class APIClient:

    def __init__(self):

        with open("config.json") as config_file:
            self.config = json.load(config_file)

        # Obtain information needed to access API from config.json
        username = self.config["spotify_username"]
        client_id = self.config["spotify_client_id"]
        client_secret = self.config["spotify_client_secret"]
        redirect_uri = self.config["spotify_redirect_uri"]

        # Connect to local database
        self.conn = sql_utils.create_sqlite_connection()

        print("Asked for token")

        # Obtain token to access API
        token = util.prompt_for_user_token(username,
                                           None,
                                           client_id,
                                           client_secret,
                                           redirect_uri)

        if token:
            print("Got token\n")
            print("Token: " + token + "\n")
            self.sp = spotipy.Spotify(auth=token)
        else:
            raise Exception("Can't get token")

        # Define dataframes to temporarily store data obtained from API

        self.album_columns = ["AlbumID", "CollectionDate", "Name", "ReleaseDate", "ImageURL"]
        self.albums_df = pd.DataFrame(columns=self.album_columns).set_index("AlbumID")

        self.artist_columns = ["ArtistID", "Name", "Popularity"]
        self.artists_df = pd.DataFrame(columns=self.artist_columns).set_index("ArtistID")

        self.artist_genre_columns = ["ArtistID", "Genre"]
        self.artists_genre_df = pd.DataFrame(columns=self.artist_genre_columns)

        self.album_artist_columns = ["AlbumID", "ArtistID"]
        self.album_artist_df = pd.DataFrame(columns=self.album_artist_columns)

        self.track_columns = ["TrackID", "SingleCollectionDate", "Name", "PreviewURL", "SingleTrackNumber",
                              "SingleReleaseDate", "SingleImageURL"]
        self.tracks_df = pd.DataFrame(columns=self.track_columns).set_index("TrackID")

        self.track_artist_columns = ["TrackID", "ArtistID"]
        self.track_artist_df = pd.DataFrame(columns=self.track_artist_columns)

        self.album_track_columns = ["AlbumID", "TrackID", "TrackNumber"]
        self.album_track_df = pd.DataFrame(columns=self.album_track_columns)

    def __del__(self):
        self.conn.close()

    # Insert new albums into local database
    def _insert_albums(self):
        albums_sql_df = pd.read_sql("SELECT AlbumID FROM Albums", self.conn).set_index("AlbumID")
        compare_df = self.albums_df.join(albums_sql_df, how="inner")
        self.albums_df = pd.concat([self.albums_df, compare_df]).drop_duplicates(keep=False)
        self.albums_df.to_sql("Albums", self.conn, if_exists="append")

    # Insert new artists into local database
    def _insert_artists(self):
        self.artists_df = self.artists_df.drop_duplicates()
        artists_sql_df = pd.read_sql("SELECT ArtistID FROM Artists", self.conn).set_index("ArtistID")
        compare_df = self.artists_df.join(artists_sql_df, how="inner")
        self.artists_df = pd.concat([self.artists_df, compare_df]).drop_duplicates(keep=False)
        self.artists_df.to_sql("Artists", self.conn, if_exists="append")

    # Insert genres related to new artists into local database
    def _insert_artist_genre(self):
        self.artists_genre_df = self.artists_genre_df.drop_duplicates()
        artists_genre_sql_df = pd.read_sql("SELECT ArtistID, Genre FROM Artist_Genre", self.conn)
        compare_df = self.artists_genre_df.merge(artists_genre_sql_df, on=["ArtistID", "Genre"])
        self.artists_genre_df = pd.concat([self.artists_genre_df, compare_df]).drop_duplicates(keep=False).set_index([
            "ArtistID",
            "Genre"
        ])
        self.artists_genre_df.to_sql("Artist_Genre", self.conn, if_exists="append")

    # Insert album to artist relationships into local database
    def _insert_album_artist(self):
        album_artist_sql_df = pd.read_sql("SELECT AlbumID, ArtistID FROM Album_Artist", self.conn)
        compare_df = self.album_artist_df.merge(album_artist_sql_df, on=["AlbumID", "ArtistID"])
        self.album_artist_df = pd.concat([self.album_artist_df, compare_df]).drop_duplicates(keep=False).set_index([
            "AlbumID",
            "ArtistID"
        ])
        self.album_artist_df.to_sql("Album_Artist", self.conn, if_exists="append")

    # Insert new tracks into local database
    def _insert_tracks(self):
        tracks_sql_df = pd.read_sql("SELECT TrackID FROM Tracks", self.conn).set_index("TrackID")
        compare_df = self.tracks_df.join(tracks_sql_df, how="inner")
        self.tracks_df = pd.concat([self.tracks_df, compare_df]).drop_duplicates(keep=False)
        self.tracks_df.to_sql("Tracks", self.conn, if_exists="append")

    # Insert track to artist relationships into local database
    def _insert_track_artist(self):
        track_artist_sql_df = pd.read_sql("SELECT TrackID, ArtistID FROM Track_Artist", self.conn)
        compare_df = self.track_artist_df.merge(track_artist_sql_df, on=["TrackID", "ArtistID"])
        self.track_artist_df = pd.concat([self.track_artist_df, compare_df]).drop_duplicates(keep=False).set_index([
            "TrackID",
            "ArtistID"
        ])
        self.track_artist_df.to_sql("Track_Artist", self.conn, if_exists="append")

    # Insert album to track relationships into local database
    def _insert_album_track(self):
        album_track_sql_df = pd.read_sql("SELECT AlbumID, TrackID FROM Album_Track", self.conn)
        compare_df = self.album_track_df.merge(album_track_sql_df, on=["AlbumID", "TrackID"])
        self.album_track_df = pd.concat([self.album_track_df, compare_df]).drop_duplicates(keep=False).set_index([
            "AlbumID",
            "TrackID"
        ])
        self.album_track_df.to_sql("Album_Track", self.conn, if_exists="append")

    # Collect data from API, parse it, and store it into a local database
    def collect_data(self):

        # Collects a number of new releases specified in the config.json file
        results = self.sp.new_releases(limit=self.config["new_release_number"])

        for item in results["albums"]["items"]:

            # Collect data for albums
            if item["album_type"] == "album":

                album_id = item["id"]
                collection_date = datetime.today().strftime("%Y-%m-%d")
                album_name = item["name"]
                release_date = item["release_date"]
                image_url = item["images"][0]["url"]
                row = pd.DataFrame([[album_id, collection_date, album_name, release_date, image_url]],
                                   columns=self.album_columns).set_index("AlbumID")
                self.albums_df = self.albums_df.append(row)

                album_tracks = self.sp.album_tracks(album_id)

                # Collect data for tracks of album
                for track in album_tracks["items"]:
                    track_id = track["id"]
                    track_name = track["name"]
                    track_number = track["track_number"]
                    track_preview = track["preview_url"]
                    row = pd.DataFrame([[track_id, None, track_name, track_preview, None, None, None]],
                                       columns=self.track_columns).set_index("TrackID")
                    self.tracks_df = self.tracks_df.append(row)

                    row = pd.DataFrame([[album_id, track_id, track_number]],
                                       columns=self.album_track_columns)
                    self.album_track_df = self.album_track_df.append(row)

                    # Collect data for artists of tracks
                    for artist in track["artists"]:
                        artist_id = artist["id"]
                        artist_name = artist["name"]
                        artist_full = self.sp.artist(artist_id)
                        artist_popularity = artist_full["popularity"]

                        row = pd.DataFrame([[artist_id, artist_name, artist_popularity]],
                                           columns=self.artist_columns).set_index("ArtistID")
                        self.artists_df = self.artists_df.append(row)

                        row = pd.DataFrame([[track_id, artist_id]],
                                           columns=self.track_artist_columns)
                        self.track_artist_df = self.track_artist_df.append(row)

                        # Collect data for genres of artists
                        for genre in artist_full["genres"]:
                            row = pd.DataFrame([[artist_id, genre]],
                                               columns=self.artist_genre_columns)
                            self.artists_genre_df = self.artists_genre_df.append(row)

                # Collect data for artists of album
                for artist in item["artists"]:

                    artist_id = artist["id"]
                    artist_name = artist["name"]
                    artist_full = self.sp.artist(artist_id)
                    artist_popularity = artist_full["popularity"]

                    row = pd.DataFrame([[artist_id, artist_name, artist_popularity]],
                                       columns=self.artist_columns).set_index("ArtistID")
                    self.artists_df = self.artists_df.append(row)

                    row = pd.DataFrame([[album_id, artist_id]],
                                       columns=self.album_artist_columns)
                    self.album_artist_df = self.album_artist_df.append(row)

                    # Collect data for genres of artists
                    for genre in artist_full["genres"]:
                        row = pd.DataFrame([[artist_id, genre]],
                                           columns=self.artist_genre_columns)
                        self.artists_genre_df = self.artists_genre_df.append(row)

            # Collect data for singles
            elif item["album_type"] == "single":
                tracks = self.sp.album_tracks(item["id"])

                track_image = item["images"][0]["url"]
                track_release_date = item["release_date"]

                for track in tracks["items"]:
                    track_id = track["id"]
                    collection_date = datetime.today().strftime("%Y-%m-%d")
                    track_name = track["name"]
                    track_number = track["track_number"]
                    track_preview = track["preview_url"]
                    row = pd.DataFrame([[track_id, collection_date, track_name, track_preview,
                                         track_number, track_release_date, track_image]],
                                       columns=self.track_columns).set_index("TrackID")
                    self.tracks_df = self.tracks_df.append(row)

                    # Collect data for artists of single
                    for artist in track["artists"]:
                        artist_id = artist["id"]
                        artist_name = artist["name"]
                        artist_full = self.sp.artist(artist_id)
                        artist_popularity = artist_full["popularity"]

                        row = pd.DataFrame([[artist_id, artist_name, artist_popularity]],
                                           columns=self.artist_columns).set_index("ArtistID")
                        self.artists_df = self.artists_df.append(row)

                        row = pd.DataFrame([[track_id, artist_id]],
                                           columns=self.track_artist_columns)
                        self.track_artist_df = self.track_artist_df.append(row)

                        # Collect data for genres of artists
                        for genre in artist_full["genres"]:
                            row = pd.DataFrame([[artist_id, genre]],
                                               columns=self.artist_genre_columns)
                            self.artists_genre_df = self.artists_genre_df.append(row)

        # Insert only the new data from dataframes into local database

        self._insert_albums()

        self._insert_artists()

        self._insert_artist_genre()

        self._insert_album_artist()

        self._insert_tracks()

        self._insert_track_artist()

        self._insert_album_track()
