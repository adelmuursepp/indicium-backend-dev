# HEX Backend

Backend for the HEX app.

**Setting up the environment and installing the required packages:**

The `requirements.txt` file has a list of packages that are needed.

To create a virtual environment: `pip install virtualenv` then `virtualenv -p python3 venv`.

To activate the virtual environment: `.\venv\Scripts\activate`.
To activate the virtual environment on Mac: `source venv/bin/activate`

To install the packages from the `requirements.txt` file: `pip install -r requirements.txt`.

**Keys**

The API needs the firebase API key and the firebase private key file.

*To specify the API key:*

1. Create a `.env` file in the root folder of the project
2. Get the API key from the Project Settings General page in the Firebase console.
3. Put `FIREBASE_API_KEY=<API_KEY>` into the `.env` file

*To specify the firebase private key file:*
1. Generate a private key file for your service account:
    - In the Firebase console, open Settings > Service Accounts.
    - Click Generate New Private Key, then confirm by clicking Generate Key.
    - Put the JSON file containing the key in the project root. Don't upload this file to github.
2. Put `GOOGLE_APPLICATION_CREDENTIALS=<PATH_TO_PRIVATE_KEY_JSON_FILE>` into the `.env` file

You can also put `FLASK_ENV=development` in the `.env` file to see debug log messages while running the flask app.

# indicium-backend-dev
