# Helix-HR

Helix-HR is an AI agent designed to help you create recruiting outreach sequences.

![Helix-HR](/images/helix-hr.png)

## Installation

### Prerequisites
Ensure you have the following installed on your machine:
- **Node.js** and **npm** for the frontend
- **Python** and **pip** for the backend

### Running the Client (Frontend)
1. Navigate to the `client` directory:
   ```sh
   cd client
   ```
2. Install dependencies:
   ```sh
   npm install
   ```
3. Run the frontend:
   ```sh
   npm run dev
   ```
4. To navigate to the frontend display, open the address displayed after running the previous step on your browser. 

### Running the Server (Backend)
1. Open a separate terminal window.
2. Navigate to the `server` directory:
   ```sh
   cd server
   ```
3. Create a virtual environment and activate it:
   ```sh
   python3 -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```
4. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
5. Set up environment variables:
   Create a `.env` file in the `server` directory and add the following:
   ```sh
   OPENAI_API_KEY=<your-api-key-here>
   SECRET_KEY=<secret-key-here>
   ```
   The `SECRET_KEY` is for Flask to sign sessions. It can be anything, but make sure it's secure.
6. Start the backend server:
   ```sh
   python3 app.py
   ```

