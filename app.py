import streamlit as st
import requests
import os

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

API_URL = os.getenv("API_URL")
API_KEY = os.getenv("API_KEY")

if not API_URL:
    st.error(
        "API_URL is missing. Please check your .env file."
    )
    st.stop()

if not API_KEY:
    st.error(
        "API_KEY is missing. Please check your .env file."
    )
    st.stop()

UPLOAD_URL = f"{API_URL}/upload"
GENERATE_URL = f"{API_URL}/generate"

# ---------------------------------------------------------
# Page configuration
# ---------------------------------------------------------

st.set_page_config(
page_title="PDF Q&A Assistant",
page_icon="",
layout="wide"
)

# ---------------------------------------------------------
# Custom styling
# ---------------------------------------------------------

st.markdown(
""" <style>

```
.stApp {
    background-color: #f7f8fa;
}

.main-title {
    font-size: 2.2rem;
    font-weight: 700;
    color: #1f2937;
    margin-bottom: 0.2rem;
}

.subtitle {
    font-size: 1rem;
    color: #6b7280;
    margin-bottom: 2rem;
}

.section-title {
    font-size: 1.15rem;
    font-weight: 600;
    color: #1f2937;
    margin-top: 1rem;
    margin-bottom: 0.7rem;
}

.document-card {
    background-color: white;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    padding: 1rem 1.2rem;
    margin-bottom: 1.2rem;
}

.answer-card {
    background-color: white;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    padding: 1.2rem;
    margin-top: 1rem;
}

.status-muted {
    color: #6b7280;
}

</style>
""",
unsafe_allow_html=True


)

# ---------------------------------------------------------
# Session state
# ---------------------------------------------------------

if "document_name" not in st.session_state:
    st.session_state.document_name = None

if "document_chunks" not in st.session_state:
    st.session_state.document_chunks = None

if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------------------------------------------------------
# Header
# ---------------------------------------------------------

st.markdown(
'<div class="main-title">PDF Q&A Assistant</div>',
unsafe_allow_html=True
)

st.markdown(
'<div class="subtitle">'
'Upload a PDF and ask questions about its contents.'
'</div>',
unsafe_allow_html=True
)

# ---------------------------------------------------------
# Sidebar
# ---------------------------------------------------------

with st.sidebar:


    st.markdown("### Document")

uploaded_file = st.file_uploader(
    "Upload a PDF",
    type=["pdf"],
    help="Choose a PDF document to use as the knowledge source."
)

if uploaded_file is not None:

    if st.button(
        "Process document",
        use_container_width=True
    ):

        headers = {
            "Authorization": f"Bearer {API_KEY}"
        }

        files = {
            "file": (
                uploaded_file.name,
                uploaded_file.getvalue(),
                "application/pdf"
            )
        }

        with st.spinner("Processing document..."):

            try:

                response = requests.post(
                    UPLOAD_URL,
                    headers=headers,
                    files=files,
                    timeout=180
                )

                if response.status_code == 200:

                    result = response.json()

                    st.session_state.document_name = result.get(
                        "filename",
                        uploaded_file.name
                    )

                    st.session_state.document_chunks = result.get(
                        "chunks"
                    )

                    st.session_state.messages = []

                    st.success(
                        "Document processed successfully."
                    )

                else:

                    try:
                        error = response.json().get(
                            "detail",
                            "An error occurred while processing the document."
                        )
                    except ValueError:
                        error = response.text

                    st.error(
                        f"Upload failed ({response.status_code}): {error}"
                    )

            except requests.exceptions.Timeout:

                st.error(
                    "The request timed out while processing the PDF."
                )

            except requests.exceptions.ConnectionError:

                st.error(
                    "Could not connect to the backend. "
                    "Make sure the Kaggle notebook and ngrok tunnel are running."
                )

            except requests.exceptions.RequestException as e:

                st.error(
                    f"Connection error: {e}"
                )

st.markdown("---")

if st.session_state.document_name:

    st.markdown("### Current document")

    st.markdown(
        f"""
        <div class="document-card">
            <strong>{st.session_state.document_name}</strong>
            <br>
            <span class="status-muted">
                {st.session_state.document_chunks} text chunks indexed
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )

else:

    st.info(
        "Upload and process a PDF to start asking questions."
    )


# ---------------------------------------------------------
# Main area
# ---------------------------------------------------------

if not st.session_state.document_name:


    st.markdown(
    """
    <div class="answer-card">
        <h3>Get started</h3>
        <p>
            Upload a PDF from the sidebar, process it, and then ask
            questions about the document.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)


else:


    st.markdown(
    '<div class="section-title">Ask a question</div>',
    unsafe_allow_html=True
)

question = st.chat_input(
    "Ask something about the document..."
)

# Display previous conversation

for message in st.session_state.messages:

    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if question:

    # Display user question

    st.session_state.messages.append(
        {
            "role": "user",
            "content": question
        }
    )

    with st.chat_message("user"):
        st.markdown(question)

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "question": question
    }

    with st.chat_message("assistant"):

        with st.spinner("Searching the document..."):

            try:

                response = requests.post(
                    GENERATE_URL,
                    headers=headers,
                    json=payload,
                    timeout=180
                )

                if response.status_code == 200:

                    result = response.json()

                    answer = result.get(
                        "response",
                        "No answer was returned."
                    )

                    st.markdown(answer)

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": answer
                        }
                    )

                    sources = result.get(
                        "sources",
                        []
                    )

                    if sources:

                        with st.expander(
                            "View retrieved document sections"
                        ):

                            for i, source in enumerate(
                                sources,
                                start=1
                            ):

                                st.markdown(
                                    f"**Source {i}**"
                                )

                                st.write(source)

                else:

                    try:
                        error = response.json().get(
                            "detail",
                            "The backend could not generate an answer."
                        )
                    except ValueError:
                        error = response.text

                    error_message = (
                        f"Request failed ({response.status_code}): "
                        f"{error}"
                    )

                    st.error(error_message)

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": error_message
                        }
                    )

            except requests.exceptions.Timeout:

                error_message = (
                    "The request timed out. "
                    "The model may still be processing the question."
                )

                st.error(error_message)

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": error_message
                    }
                )

            except requests.exceptions.ConnectionError:

                error_message = (
                    "Could not connect to the backend. "
                    "Make sure the Kaggle notebook is still running "
                    "and the ngrok tunnel is active."
                )

                st.error(error_message)

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": error_message
                    }
                )

            except requests.exceptions.RequestException as e:

                error_message = f"Connection error: {e}"

                st.error(error_message)

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": error_message
                    }
                )