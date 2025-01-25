import logging
import azure.functions as func
import csv
import os
import json
import requests
import zipfile
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = func.FunctionApp()

@app.timer_trigger(schedule="0 0 6 * * *", arg_name="myTimer", run_on_startup=False,
              use_monitor=False) 
def func_timer_trigger(myTimer: func.TimerRequest) -> None:
    if myTimer.past_due:
        logging.info('The timer is past due!')
        all_trades_url = os.getenv('all_trades_url', '')
        trader_name = os.getenv('trader_name', '')
        sender_email = os.getenv('sender_email', '')
        app_password = os.getenv('app_password', '')
        recipient_email = os.getenv('recipient_email', '')
        pdf_file_url = os.getenv('pdf_file_url', '')

        try:
            os.makedirs('./trades/2025FD')
        except FileExistsError:
            pass

        new_trades = []
        new_trades = check_for_new_trades(all_trades_url, trader_name)

        # check if new_trades conains any trades for today
        new_trades_today = [trade for trade in new_trades if trade[0].date() == datetime.datetime.now().date()]
        if new_trades_today:
            print('There are new trades today')
            # Send an email notification
            send_email_notification(new_trades, trader_name, sender_email, app_password, recipient_email, pdf_file_url)

    remove_old_files(new_trades)
    logging.info('Trader trigger function executed.')


def check_for_new_trades(all_trades_url, trader_name):
    # Check if ./trades/2025FD.zip file exists
    # If not, download zip file
    if not os.path.isfile('./trades/2025FD.zip'):
        r = requests.get(all_trades_url)
        with open('./trades/2025FD.zip', 'wb') as f:
            f.write(r.content)

        # Unzip the file
        with zipfile.ZipFile('./trades/2025FD.zip', 'r') as zip_ref:
            zip_ref.extractall('./trades/2025FD')

    new_trades = []

    # Read the csv fil in the zip file
    with open('./trades/2025FD/2025FD.txt', 'r') as f:
        for line in csv.reader(f, delimiter='\t'):
            if line[1] == trader_name:
                dt = datetime.datetime.strptime(line[-2], '%m/%d/%Y')
                doc_id = line[8]
                new_trades.append((dt, doc_id))

    # Sort trades by date, most recent first
    new_trades.sort(reverse=True)

    return new_trades


def send_email_notification(trades, trader_name, sender_email, app_password, recipient_email, pdf_file_url):
    if not trades:
        return

    subject = f"New {trader_name} Trades Detected"
    body = "New trades have been detected:\n\n"

    for trade in trades:
        body += f"Date: {trade[0].strftime('%Y-%m-%d')}\n"
        body += f"Document ID: {trade[1]}\n"
        body += f"PDF URL: {pdf_file_url}{trade[1]}.pdf\n\n"

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, app_password)
        text = msg.as_string()
        server.sendmail(sender_email, recipient_email, text)
        server.quit()
        print(f"Email notification sent for {len(trades)} trades")
    except Exception as e:
        print(f"Failed to send email notification: {e}")

def remove_old_files(new_trades):
    files_to_remove = [
        './trades/2025FD.zip',
        './trades/2025FD/2025FD.txt',
        './trades/2025FD/2025FD.xml'
    ]
    
    for file in files_to_remove:
        if os.path.exists(file):
            os.remove(file)
        else:
            print(f"File not found: {file}")
    
    if new_trades:
        for trade in new_trades:
            trade_file = f'./trades/2025FD/{trade[1]}.pdf'
            if os.path.exists(trade_file):
                os.remove(trade_file)
            else:
                print(f"File not found: {trade_file}")