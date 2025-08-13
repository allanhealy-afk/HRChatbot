# Chat2SQL App

This is a natural language interface that converts user queries into SQL, executes them against a local SQLite database, and returns user-friendly responses. It's built using Python, Streamlit, and CalypsoAI's PromptAPI.

---

## 🚀 Features

- Converts natural language to SQL queries using an LLM (via CalypsoAI PromptAPI)
- Executes queries against a SQLite database
- Returns clean, human-readable answers
- Includes a simple Streamlit web interface

---

## ⚙️ Prerequisites

Before running the app, make sure you have the following installed:

- Python 3.8 or newer
- `pip` for installing dependencies
- A valid `CALYPSO_API_KEY` set as an environment variable
- A provider name that you have configured in CalypsoAI

---

## 📦 Installation

1. **Clone the repository** (or download the project files):

```bash
git clone https://gitlab.com/your-org/chat2sqlapp.git
cd chat2sqlapp
```

2.	**Create a virtual environment** (optional but recommended):

```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```
3.	**Install dependencies:**

```bash
pip install -r requirements.txt
```

4.	**Set up your environment variables:**

Create a .env file in the project root and add:

```bash
CALYPSO_API_KEY=your_calypso_api_key_here
```

⸻

## 🗃️ Create the Database

Before running the app, generate the sample SQLite database:

```bash
python createdb.py
```

This will create a database.db file with some sample data for testing.

⸻

## 🧪 Run the App

Start the Streamlit app:

streamlit run app.py

Then go to http://localhost:8501 in your browser to use the interface.

⸻

❗ Notes
	•	Ensure your API key is valid and has access to the PromptAPI service.
	•	The app uses the gpt-4o-mini model by default. You can change this by modifying the provider value in app.py.
	•	SQL injection and prompt safety are handled via the API’s moderation layer, but always exercise caution when executing queries.

⸻

🧼 Example Queries
	•	“List all employees with salaries above 80,000”
	•	“Show all department names”
	•	“How many records are in the employees table?”

⸻

## 📮 Feedback

Open issues or feature requests are welcome via GitLab Issues.

---

Let me know if you’d like a `requirements.txt` generated or want this README committed to your project directly.