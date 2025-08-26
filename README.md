# Agentic AI Virtual Stylist System

## Project Overview
This project is an agentic AI-based virtual stylist system. It is designed to assist users in getting personalized outfit recommendations based on their text descriptions. The system is built using Python for the backend and standard web technologies (HTML, CSS, JavaScript) for the frontend.

## System Components

### 1. Backend (`backend/`)
This is where the core logic of the multi-agent system resides. It is built using the Flask framework to create a RESTful API. The backend contains three intelligent agents that communicate with each other via internal Python function calls.

- **`main.py`**: The main application file. It contains the code for all three agents, the API endpoint, and the server logic.
- **Agent Roles:**
    - **User Interaction Agent:** Processes user requests using basic NLP-like techniques.
    - **Fashion IR Agent:** Retrieves relevant fashion data from a mock knowledge base.
    - **Style Recommendation Agent:** Generates the final recommendation based on the combined information.

### 2. Frontend (`frontend/`)
This is the user-facing part of the application. It consists of a single HTML file that uses JavaScript to interact with the backend API.

- **`index.html`**: Contains the user interface, including the text input form and the display area for recommendations.

### 3. Virtual Environment (`venv/`)
This folder contains the isolated Python environment for the project.

## Setup Instructions

### Step 1: Set up the Virtual Environment

1.  Open your terminal or command prompt.
2.  Navigate to your project root directory (`virtual-stylist`).
3.  Create the virtual environment (if it doesn't exist):
    ```bash
    python -m venv venv
    ```
4.  Activate the virtual environment:
    -   On Windows:
        ```bash
        venv\Scripts\activate
        ```
    -   On macOS/Linux:
        ```bash
        source venv/bin/activate
        ```

### Step 2: Install Dependencies

1.  While the virtual environment is active, navigate to the `backend` folder.
2.  Install the required Python packages:
    ```bash
    pip install Flask Flask-Cors
    ```
    * `Flask` is the web framework for the backend API.
    * `Flask-Cors` is necessary to allow the frontend to communicate with the backend.

### Step 3: Run the Application

1.  Make sure you are still in the `backend` directory with the virtual environment activated.
2.  Run the main Python file:
    ```bash
    python app.py
    ```
    You should see a message in your terminal indicating that the Flask server is running at `http://127.0.0.1:5000`.

### Step 4: Access the Frontend

1.  Open your web browser.
2.  Go to the URL: `http://127.0.0.1:5000`
3.  You will see the user interface. Enter a query and click "Get Styled" to see the system in action.


