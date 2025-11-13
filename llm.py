import lmstudio as lms
from pydantic import BaseModel


# A class based schema for a book
class AddressSchema(BaseModel):
    house_number: str
    street_name: str
    district: str
    city: str
    state: str
    postal_code: str
    country: str


prompt = """
    Find the address in the following text. 
    Return the address as a JSON structure with attributes for house number, street name, district, city, state, postcode and country
"""
text = """
Compound Code(s): 	ASP8062
Trial Phase: 	Phase I
Sponsor Name and Address: 	Astellas Pharma
    Global Development Inc.
    1 Astellas Way Northbrook, IL 60062, US
    Regulatory Agency Identifier Number(s):
    IND 146215
"""
model = lms.llm("openai/gpt-oss-20b")
result = model.respond(f"{prompt} '{text}'", response_format=AddressSchema)
address = result.parsed
print(address)
