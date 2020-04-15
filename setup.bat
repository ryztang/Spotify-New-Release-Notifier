call <Enter-path-to-miniconda-or-anaconda>\Scripts\activate.bat <Enter-path-to-miniconda-or-anaconda>
call conda create --name Spotify-New-Release-Notifier
call conda activate Spotify-New-Release-Notifier
call conda install pip
call pip install spotipy
call conda install pandas