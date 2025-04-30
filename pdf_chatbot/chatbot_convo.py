from openai import OpenAI

# Initialise OpenAI client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="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",  
)

# Initialise conversation history
conversation_history = [
    {"role": "system", "content": "You are a helpful assistant."}
]

# Given user input, it interacts with the OpenAI API and returns the assistant's response
def get_chatbot_response(user_input):
    # Add user message to history
    conversation_history.append({"role": "user", "content": user_input})

    try:
        # Get streaming response from OpenAI
        stream = client.chat.completions.create(
            model="deepseek/deepseek-r1:free",
            messages=conversation_history,
            stream=True
        )

        # Collect response chunks
        full_response = []
        for chunk in stream:
            content = chunk.choices[0].delta.content or ""
            full_response.append(content)

        assistant_response = "".join(full_response)

        # Add assistant response to history
        conversation_history.append({
            "role": "assistant",
            "content": assistant_response
        })

        return assistant_response

    except Exception as e:
        return f"Error: {str(e)}"
