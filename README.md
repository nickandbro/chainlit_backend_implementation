# Chainlit Backend Implementation

This project is a reverse-engineered version of Chainlit's cloud, offering limited functionality. It focuses on enabling the saving of conversations, messages, and adding new users to a Chainlit-like application without using chainlit's cloud.

### Prerequisites

- Python 3.x
- pip (Python package manager)
- Git

### Installation

1. **Clone the Repository**

   Clone the project repository to your local machine.
   ```bash
   git clone https://github.com/nickandbro/chainlit_backend_implementation
   cd chainlit_backend_implementation
   ```
2. **Set Up a Virtual Environment**

    Create and activate a virtual environment for the project.
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On macOS/Linux
    ```
3. **Install Chainlit**

    If you haven't installed chainlit, install version 0.7.700 as its the last proven version that works
    ```bash
    pip install chainlit==0.7.700
    ```
4. **Install Other Dependencies**

    Install the required dependencies from the requirements.txt file.
    ```bash
    pip install -r requirements.txt
    ```
5. **Environment Variables**
    Set the following environment variables for your chainlit client:
    ```bash
    CHAINLIT_AUTH_SECRET="EMPTY"
    CHAINLIT_API_KEY="your key"
    CHAINLIT_SERVER="http://127.0.0.1:5000"
    ```
6. **Run the Server**

    To run the server, use the following command:
    ```bash
    uvicorn main:app --port 5000 
    ```
    Add --host 0.0.0.0 if you want to host publicly 

# Current Problems
    1. Currently limited to just saving/retrieving/deleting conversations and creating/gettings users
    2. Relies on version 0.7.700 for compatibility. Most likely chainlit 1.0.0 is going to use a completely different graphQL schema 

   
