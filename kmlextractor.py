from fastkml import kml
import csv

def extract_extended_data(placemark):
    extended_data = placemark.extended_data.elements
    attributes = {}

    for data in extended_data:
        if hasattr(data, 'schema_data'):
            for simple_data in data.schema_data:
                attributes[simple_data.name] = simple_data.text

    return attributes

def kml_to_csv(kml_file, csv_file):
    with open(kml_file, 'rt', encoding="utf-8") as f:
        doc = f.read()
    k = kml.KML()
    k.from_string(doc)
    features = list(k.features())
    placemarks = list(features[0].features())

    with open(csv_file, 'w', newline='', encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Name', 'Description', 'Schlamms_01', 'Messpunkt', 'schlammspiegel_mai', 'Coordinates'])

        for pm in placemarks:
            name = pm.name
            description = pm.description
            

            extended_data = extract_extended_data(pm)
            attribute1 = extended_data.get('Schlamms_01', '')
            attribute2 = extended_data.get('Messpunkt', '')
            attribute3 = extended_data.get('schlammspiegel_mai', '')
            
            coords = pm.geometry.coords
            writer.writerow([name, description, attribute1, attribute2, attribute3, coords[0]])


input_kml_file = input("Enter the path to the input KML file: ")
output_csv_file = input("Enter the path for the output CSV file: ")

kml_to_csv(input_kml_file, output_csv_file)
