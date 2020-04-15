from api_client import APIClient

from email_notifier import EmailNotifier


def main():

    # First, collect data from Spotify API into a local database
    try:
        spotify_client = APIClient()
        spotify_client.collect_data()
        print("Data collected from Spotify\n")
    except Exception as e:
        print("Exception: " + str(e))

    # Next, send an email notification to the recipients specified in the config database
    try:
        notifier = EmailNotifier()

        new_data = notifier.get_data_to_send()

        # Send email only if there are new releases to send
        if new_data:
            notifier.send_email()
            print("Email sent")
        else:
            print("No new releases")

    except Exception as e:
        print("Exception: " + str(e))


if __name__ == "__main__":
    main()
