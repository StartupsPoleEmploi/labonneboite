from typing import Optional


class IncorrectAdressDataException(Exception):
    pass


def get_full_adress(
    street_number: Optional[str], street_name: Optional[str], zipcode: Optional[str], city: Optional[str]
):
    if city and "arrondissement" in city.lower():
        city = city.split(" ")[0]
        if city.lower() not in ["paris", "lyon", "marseille"]:
            raise IncorrectAdressDataException

    if street_name and "LIEU DIT " in street_name:
        street_name = street_name.replace("LIEU DIT ", "")
        street_number = ""

    full_address = " ".join(filter(None, (street_number, street_name, zipcode, city)))
    return full_address.strip()
