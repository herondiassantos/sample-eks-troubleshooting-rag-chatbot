import boto3
import json
    
def invoke_claude(prompt_text):
    """
    Invokes the Claude model via Bedrock with the given prompt text.
    
    :param prompt_text: The input prompt for the model.
    :return: The response from the Claude model.
    """
    # Initialize the Bedrock client
    bedrock_client = boto3.client(service_name='bedrock-runtime')

    # Define the request body for the Claude model
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1000,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt_text
                    }
                ]
            }
        ]
    }

    # Invoke the Claude model through the Bedrock API
    response = bedrock_client.invoke_model(
        modelId='anthropic.claude-3-sonnet-20240229-v1:0',
        contentType='application/json',
        accept='application/json',
        body=json.dumps(body)
    )
    
    # Parse the model's response
    response_body = json.loads(response['body'].read())
    response_text = response_body['content'][0]['text']
    
    return response_text