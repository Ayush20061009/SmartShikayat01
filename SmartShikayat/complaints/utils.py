import random

# Dummy Database: Plate Number -> Owner Email
DUMMY_VEHICLE_DB = {
    "GJ01AB1234": "owner1@example.com",
    "MH12CD5678": "owner2@example.com",
    "DL3CDE9012": "talaviyadharmik73@gmail.com",
    "GJ05XY9876": "violation@smartcity.com",
}

def mock_ocr(image):
    """
    Simulates OCR by returning a random plate from the DB 
    or a specific one if 'test' is in the filename.
    """
    if not image:
        return None
        
    # For testing: if filename contains 'test', return a specific plate
    if 'test' in image.name.lower():
        return "DL3CDE9012"
        
    # Default behavior: Random choice to simulate detection
    return random.choice(list(DUMMY_VEHICLE_DB.keys()))

def get_vehicle_owner_email(plate_number):
    """
    Returns the email associated with the plate number.
    """
    return DUMMY_VEHICLE_DB.get(plate_number)

