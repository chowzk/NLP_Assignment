from openai import OpenAI
from flask import Response
from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

# Initialise OpenAI client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="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",
    # api_key="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",  # exceed limit
)

# Initialise conversation history
conversation_history = [
    {"role": "system", "content": "You are a helpful assistant."}
]

def get_chatbot_response(user_input, conversation_history, full_response, chat_id, db, app):
    conversation_history.append({"role": "user", "content": user_input})
    try:
        stream = client.chat.completions.create(
            model="deepseek/deepseek-r1:free",  # Verify this model name with OpenRouter
            #messages=[{"role": "user", "content": user_input}],
            messages=conversation_history,
            stream=True
        )
        full_response = []
        def generate():
            for chunk in stream:
                content = chunk.choices[0].delta.content or ""
                full_response.append(content)
                yield content.encode('utf-8')
            # Append assistant response to history after streaming
            assistant_content = "".join(full_response)
            conversation_history.append({
                "role": "assistant",
                "content": assistant_content
            })
            # Save assistant message to database
            with app.app_context():
                from app import Message  # Import here to avoid circular import
                assistant_message = Message(
                    chat_id=chat_id,
                    role="assistant",
                    content=assistant_content,
                    timestamp=datetime.now(timezone.utc)
                )
                db.session.add(assistant_message)
                db.session.commit()
        return Response(generate(), mimetype='text/plain')
    except Exception as e:
        print(f"Error in get_chatbot_response: {str(e)}")
        return Response("Server is busy. Please try again later.", mimetype='text/plain')



# # Given user input, it interacts with the OpenAI API and returns the assistant's response
# def get_chatbot_response(user_input):
#     # Add user message to history
#     conversation_history.append({"role": "user", "content": user_input})

#     try:
#         # Get streaming response from OpenAI
#         stream = client.chat.completions.create(
#             model="deepseek/deepseek-r1:free",
#             messages=conversation_history,
#             stream=True
#         )

#         # Collect response chunks
#         full_response = []
#         for chunk in stream:
#             content = chunk.choices[0].delta.content or ""
#             full_response.append(content)

#         assistant_response = "".join(full_response)

#         # Add assistant response to history
#         conversation_history.append({
#             "role": "assistant",
#             "content": assistant_response
#         })

#         return assistant_response

#     except Exception as e:
#         return f"Error: {str(e)}"
