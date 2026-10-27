import os, json, re
from dotenv import load_dotenv

# Add references
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient


def print_workflow_output(output_text):
    decoder = json.JSONDecoder()
    pos = 0
    ticket_number = 1
    found_any = False

    while pos < len(output_text):
        # Procura o início do próximo JSON
        match = re.search(r"\{", output_text[pos:])
        if not match:
            break

        start_idx = pos + match.start()

        try:
            # Decodifica o JSON respeitando chaves aninhadas
            ticket, end_idx = decoder.raw_decode(output_text, idx=start_idx)
            found_any = True

            # O texto após o JSON até o próximo JSON (ou até o fim)
            pos = end_idx
            next_match = re.search(r"\{", output_text[pos:])
            next_start = pos + next_match.start() if next_match else len(output_text)
            response_text = output_text[pos:next_start]

            # Exibe o ticket formatado
            print("\n" + "=" * 80)
            category = ticket.get('category', 'N/A')
            confidence = ticket.get('confidence', 0)
            print(f"Ticket {ticket_number}: {category} ({confidence:.0%} confidence)")
            print("-" * 80)
            print(f"Issue: {ticket.get('customer_issue', 'N/A')}")
            print("\nResponse:")
            print(response_text.strip())
            print("=" * 80 + "\n")

            ticket_number += 1
            pos = next_start

        except json.JSONDecodeError:
            # Caso encontre uma chave que não é um JSON válido, avança 1 caractere
            pos = start_idx + 1

    if not found_any:
        print(output_text)

load_dotenv()
endpoint = os.environ["PROJECT_ENDPOINT"]

# Connect to the AI Project client
# Connect to the AI Project client
with (
    DefaultAzureCredential() as credential,
    AIProjectClient(endpoint=endpoint, credential=credential) as project_client,
    project_client.get_openai_client() as openai_client,
):

    # Specify the workflow
    workflow = {
        "name": "ContosoPay-Customer-Support-Triage"
    }
    

    # Create a conversation and run the workflow
    conversation = openai_client.conversations.create()
    print(f"Created conversation (id: {conversation.id})")

    stream = openai_client.responses.create(
        conversation=conversation.id,
        extra_body={"agent_reference" : {"name" : workflow["name"], "type": "agent_reference"}},
        input="Start",
        stream=True,
    )


    # Process events from the workflow run
    for event in stream:
        if (event.type == "response.completed"):
            print("\nResponse completed:")
            response = openai_client.responses.retrieve(event.response.id)
            print_workflow_output(response.output_text)
 

    # Clean up resources
    openai_client.conversations.delete(conversation_id=conversation.id)
    print("\nConversation deleted")

