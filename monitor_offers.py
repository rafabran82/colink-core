import time
import xrpl
from xrpl.models.requests import AccountOffers
from xrpl.wallet import Wallet
import logging
from smtplib import SMTP
from email.mime.text import MIMEText

# Set up wallet using the private key (base58)
private_key = 'sEdTDuiZRvhS6EhzcnkeqkxAfhuFQ6q'  # Replace with your private key
wallet = Wallet.from_seed(private_key)

# Set up logging
logging.basicConfig(filename='offer_monitor_log.txt', level=logging.INFO)

# Function to send email alerts
def send_alert(subject, body):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = 'your_email@example.com'  # Replace with your email
    msg['To'] = 'recipient_email@example.com'  # Replace with recipient's email

    try:
        server = SMTP('smtp.example.com')  # Replace with your SMTP server
        server.starttls()
        server.login('your_email@example.com', 'your_password')  # Replace with email and password
        server.sendmail(msg['From'], msg['To'], msg.as_string())
        server.quit()
        print("Alert sent successfully!")
    except Exception as e:
        print(f"Error sending alert: {e}")

# Define the function to monitor offers
def monitor_offers():
    while True:
        # Fetch the offers for the account
        account_offers = AccountOffers(account=wallet.classic_address)

        # Print and log the active offers
        offer_details = f"Active Offers for {wallet.classic_address}: {account_offers}"
        print(offer_details)
        logging.info(offer_details)

        # Check if any offer has been filled or matched
        if account_offers.result['offers']:
            send_alert('Offer Created', f'Offer created successfully for {wallet.classic_address}.')

        # Sleep for 30 seconds before checking again
        time.sleep(30)

# Start monitoring
monitor_offers()
