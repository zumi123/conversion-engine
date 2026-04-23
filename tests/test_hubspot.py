from hubspot import HubSpot
from hubspot.crm.contacts import SimplePublicObjectInputForCreate
from dotenv import load_dotenv
import os

load_dotenv()

client = HubSpot(access_token=os.environ["HUBSPOT_API_KEY"])

def create_test_contact():
    contact = SimplePublicObjectInputForCreate(
        properties={
            "firstname": "Test",
            "lastname": "Prospect",
            "email": "test.prospect@company.com",
            "company": "Test Company",
            "phone": "+251920100142"
        }
    )
    
    response = client.crm.contacts.basic_api.create(
        simple_public_object_input_for_create=contact
    )
    
    print("Contact created:", response.id)
    print("Properties:", response.properties)
    return response

create_test_contact()