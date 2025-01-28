import logging
import azure.functions as func
import csv
import os
import requests
import zipfile
import datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

app = func.FunctionApp()

# Helper function to download a file
def download_file(url, output_dir):
    # Ensure the output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logging.info(f"Created directory '{output_dir}'")

    # Get the file name from the URL
    file_name = os.path.join(output_dir, os.path.basename(url))

    # Download the file
    with requests.get(url, stream=True, timeout=5) as r:
        r.raise_for_status()
        with open(file_name, 'wb') as f:
            f.write(r.content)

    logging.info(f"Downloaded '{url}' to '{file_name}'")

    return file_name

# Helper function to unzip a file
def unzip_file(zip_file_path):
    # Ensure the file exists
    if not os.path.exists(zip_file_path):
        raise FileNotFoundError(f"File '{zip_file_path}' not found.")
    
    # Get the directory of the zip file
    output_dir = os.path.dirname(zip_file_path)

    # Unzip the file
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall(output_dir)
        logging.info(f"Unzipped '{zip_file_path}' to '{output_dir}'")

# Helper function to send an email notification
def send_email_notification(trades, trader_name, sender_email, recipient_email, pdf_file_url):
    subject = f"New {trader_name} Trades Detected"
    body = f"New Nancy {trader_name} trades have been detected:\n\n"

    for trade in trades:
        body += f"Date: {trade[0].strftime('%Y-%m-%d')}\n"
        body += f"Document ID: {trade[1]}\n"
        body += f"PDF URL: {pdf_file_url}{trade[1]}.pdf\n\n"

    msg = Mail(
        from_email=sender_email,
        to_emails=recipient_email,
        subject=subject,
        plain_text_content=body
    )

    akey = os.getenv('key', '')
    try:
        sg = SendGridAPIClient(api_key=akey)
        response = sg.client.mail.send.post(request_body=msg.get())
        logging.info(
            "Email notification sent for %d trades %d", len(trades), response.status_code)
        print(f"Email notification sent for {len(trades)} trades")
    except Exception as e:
        print(f"Failed to send email notification: {e}")
        logging.error(f"Failed to send email notification: {e}")

# Helper function to remove old files
def remove_old_files(trades):
    files_to_remove = [
        '/tmp/trades/2025FD.zip',
        '/tmp/trades/2025FD/2025FD.zip',
        '/tmp/trades/2025FD/2025FD.txt',
        '/tmp/trades/2025FD/2025FD.xml'
    ]

    for file in files_to_remove:
        if os.path.exists(file):
            os.remove(file)
        else:
            print(f"File not found: {file}")

    if trades:
        for trade in trades:
            trade_file = f'/tmp/trades/2025FD/{trade[1]}.pdf'
            if os.path.exists(trade_file):
                os.remove(trade_file)
            else:
                print(f"File not found: {trade_file}")

# Check for new trades
def check_for_new_trades(all_trades_url, trader_name):
    # Check if ./trades/2025FD.zip file exists
    # If not, download zip file
    if not os.path.isfile('/tmp/trades/2025FD.zip'):
        r = requests.get(all_trades_url)
        with open('/tmp/trades/2025FD.zip', 'wb') as f:
            f.write(r.content)

        # Unzip the file
        with zipfile.ZipFile('/tmp/trades/2025FD.zip', 'r') as zip_ref:
            zip_ref.extractall('/tmp/trades/2025FD')

    trades = []

    # Read the csv file in the zip file
    with open('/tmp/trades/2025FD/2025FD.txt', 'r') as f:
        for line in csv.reader(f, delimiter='\t'):
            if line[1] == trader_name:
                dt = datetime.datetime.strptime(line[-2], '%m/%d/%Y')
                doc_id = line[8]
                trades.append((dt, doc_id))

    # Sort trades by date, most recent first
    # if new_trades is not empty
    if trades:
        trades.sort(reverse=True)

    return trades

# Timer trigger function
@app.timer_trigger(schedule="0 0 */6 * * *", arg_name="myTimer", run_on_startup=False,
                   use_monitor=False)
def func_timer_trigger(myTimer: func.TimerRequest) -> None:
    if myTimer.past_due:
        logging.info("The timer is past due!")

    all_trades_url = os.getenv('all_trades_url', '')
    trader_name = os.getenv('trader_name', '')
    sender_email = os.getenv('sender_email', '')
    recipient_email = os.getenv('recipient_email', '')
    pdf_file_url = os.getenv('pdf_file_url', '')

    # Ensure the output directory exists
    if not os.path.exists('/tmp/trades/2025FD'):
        os.makedirs('/tmp/trades/2025FD')
        logging.info(f"Created directory '/tmp/trades/2025FD'")
    
    download_file(all_trades_url,output_dir='/tmp/trades/2025FD')

    logging.info(f'Trader trigger function executed. {all_trades_url}')

    unzip_file(zip_file_path='/tmp/trades/2025FD/2025FD.zip')

    trades = check_for_new_trades(all_trades_url, trader_name)
    new_trades_today = [trade for trade in trades if trade[0].date() == datetime.datetime.now().date()]
    
    #TEST ONLY - TO REMOVE
    #new_trades_today = [trade for trade in trades if trade[0].date() == datetime.datetime.strptime('2025-01-17', '%Y-%m-%d').date()]

    if(new_trades_today):
        # if new_trades is not em
        if trades:
            logging.info('Found new trades today. Sending email notification.')
            send_email_notification(trades, trader_name, sender_email, recipient_email, pdf_file_url)
    else:
        logging.info('No new trades today')

    remove_old_files(trades)
    logging.info('Tadeusz Trader trigger function executed.')