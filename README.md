# Azure Function App for Trade Notifications

This Azure Function App checks for new trades and sends email notifications if new trades are detected. It also removes old trade files.

## Features

- Downloads trade files from a specified URL
- Unzips the downloaded files
- Checks for new trades
- Sends email notifications for new trades
- Removes old trade files

## Prerequisites

- Python 3.6 or later
- Azure Functions Core Tools
- An Azure account

## Setup

1. Clone the repository:

    ```bash
    git clone https://github.com/yourusername/your-repo.git
    cd your-repo
    ```

2. Create a virtual environment and activate it:

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. Install the required packages:

    ```bash
    pip install -r requirements.txt
    ```

4. Set up environment variables:

    ```bash
    export all_trades_url="your_all_trades_url"
    export trader_name="your_trader_name"
    export sender_email="your_sender_email"
    export recipient_email="your_recipient_email"
    export pdf_file_url="your_pdf_file_url"
    ```

## Usage

1. Run the Azure Function locally:

    ```bash
    func start
    ```

2. Deploy the Azure Function to Azure:

    ```bash
    func azure functionapp publish <YourFunctionAppName>
    ```

## Functions

### `download_file(url, output_dir)`

Downloads a file from the specified URL to the specified output directory.

### `unzip_file(zip_file_path)`

Unzips the specified zip file.

### `send_email_notification(trades, trader_name, sender_email, recipient_email, pdf_file_url)`

Sends an email notification with the details of the new trades.

### `remove_old_files(new_trades)`

Removes old trade files.

### [check_for_new_trades(all_trades_url, trader_name)](http://_vscodecontentref_/1)

Checks for new trades from the specified URL.

### [func_timer_trigger(myTimer: func.TimerRequest)](http://_vscodecontentref_/2)

Timer trigger function that checks for new trades and sends email notifications.

## License

This project is licensed under the MIT License - see the [LICENSE](http://_vscodecontentref_/3) file for details.