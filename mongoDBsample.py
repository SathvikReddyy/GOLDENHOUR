from pymongo import MongoClient
import os

from dotenv import load_dotenv

load_dotenv(r"C:\Users\vinis\OneDrive\Documents\Desktop\Golden Hour\GOLDENHOUR\.env")
URL = os.getenv("MONGO_URI")
print(URL)
# client = MongoClient(URL)
# db=client["ambulance_dispatch"]
# patients=db["patients"]

# patients.insert_one({
#     "name": "sathvik",
#     "location": "bowenpally",
#     "priority": "low"
# })
# for patient in patients.find():
#     print(patient)