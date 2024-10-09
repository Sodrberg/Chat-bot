import anthropic

client = anthropic.Anthropic()

response = client.beta.prompt_caching.messages.create(
    model="claude-3-5-sonnet-20240620",
    max_tokens=1024,
    system=[
      {
        "type": "text", 
        "text": "You are an AI assistant tasked with analyzing literary works. Your goal is to provide insightful commentary on themes, characters, and writing style.\n",
      },
      {
        "type": "text", 
        "text": "<the entire contents of 'Pride and Prejudice'>",
        "cache_control": {"type": "ephemeral"}
      }
    ],
    messages=[{"role": "user", "content": "Analyze the major themes in 'Pride and Prejudice'."}],
)
print(response)