from datetime import datetime

def validate_birthdate(date_str):
    # Define possible date formats
    date_formats = [
        "%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d",
        "%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y",
        "%m-%d-%Y", "%m/%d/%Y", "%m.%d.%Y",
        "%Y-%d-%m", "%Y/%d/%m", "%Y.%d.%m",
        "%d-%Y-%m", "%d/%Y/%m", "%d.%Y.%m",
        "%m-%d-%y", "%m/%d/%y", "%m.%d.%y",
        "%d-%m-%y", "%d/%m/%y", "%d.%m.%y",
    ]

    for date_format in date_formats:
        try:
            # Attempt to parse the date string with the current format
            date_obj = datetime.strptime(date_str, date_format)
            # Check if the parsed date string matches the original
            if date_obj.strftime(date_format) == date_str:
                return True
        except ValueError:
            # Continue to the next format if current one fails
            continue
    
    return False
