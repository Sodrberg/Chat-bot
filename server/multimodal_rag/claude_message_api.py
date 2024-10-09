import os
import anthropic
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('ANTHROPIC_API_KEY')
client = anthropic.Anthropic()

def get_claude_recommendation(query, query_answers):
    formatted_answers = "\n".join([f"Page {answer['metadata']['chunk_index']}: {answer['page_content']}" for answer in query_answers])
    
    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=1000,
            temperature=0,
            system="You are an expert manual writer.",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"""Based on the following query and potential answers from a motorcycle manual, select the most relevant page number.

Query: {query}

Potential answers:
{formatted_answers}

only provide the actual page number not the index. Dont provide any other text than the page number."""
                        }
                    ]
                }
            ]
        )
        
        claude_response = message.content[0].text.strip()
        print(f"Claude's response: {claude_response}")
        
        # Try to convert Claude's response to an integer
        try:
            return int(claude_response)
        except ValueError:
            print(f"Claude's response couldn't be converted to an integer: {claude_response}")
            return None
    except Exception as e:
        print(f"Error in get_claude_recommendation: {str(e)}")
        return None