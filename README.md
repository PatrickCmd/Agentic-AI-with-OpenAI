# RAG Agentic AI with OpenAI

This is a Streamlit application that demonstrates Retrieval-Augmented Generation (RAG) and agentic AI capabilities using the OpenAI API. The application allows users to interact with a conversational AI assistant enhanced with various tools such as web search, file search, and function calling.

## Features

- **Chat Interface**: Conversational interface with markdown support and conversation history
- **Web Search**: Search the web for real-time information
- **Vector Store Management**: Create vector stores and upload files for retrieval
- **File Search**: Query documents in your knowledge base
- **Function Calling**: Execute specific functions like getting weather information
- **Toggleable Tools**: Enable/disable tools via the sidebar
- **Conversation History**: Persist and display the conversation history

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd openai-api-sdk
```

2. Install the dependencies:
```bash
pip install -r app/requirements.txt
```

3. Create a `.env` file in the `app` directory with your OpenAI API key:
```
OPENAI_API_KEY=your_openai_api_key_here
```

## Usage

1. Start the Streamlit application:
```bash
cd app
streamlit run main.py
```

2. Open your browser and navigate to `http://localhost:8501`

3. Configure your tools in the sidebar:
   - Enter your OpenAI API key (if not set in the `.env` file)
   - Toggle tools on/off (Web Search, File Search, Function Calling)
   - For File Search, create a vector store and upload files

4. Chat with the AI assistant using the input field at the bottom of the screen.

## File Structure

```
openai-api-sdk/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── components/
│   │   ├── __init__.py
│   │   ├── chat_interface.py
│   │   ├── sidebar.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── vectorstore_utils.py
│   │   ├── api_utils.py
│   │   ├── conversation_utils.py
│   ├── assets/
│   │   ├── styles.css
│   ├── .env
│   └── requirements.txt
└── README.md
```

## How It Works

1. **Vector Store Creation**: Create a vector store to store and index your documents.
2. **File Upload**: Upload files (PDF, TXT, MD, DOCX) to the vector store.
3. **Web Search**: Perform real-time web searches for current information.
4. **Function Calling**: Execute specific functions like retrieving weather information.
5. **RAG Integration**: The application combines retrieved information with generative capabilities to provide accurate and up-to-date responses.

## Dependencies

- streamlit: Web application framework
- openai: OpenAI API client
- PyPDF2: PDF processing library
- python-dotenv: Environment variables management
- tqdm: Progress bar
- nest_asyncio: Nested asyncio event loop

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- OpenAI for providing the API
- Streamlit for the web application framework
