import json

# Load the JSON data from the file (updated to match determine_category.py output)
with open('output_new/recommendation_links.json', 'r') as file:
    data = json.load(file)

# Open a text file to write the links
with open('output_links.txt', 'w') as output_file:
    for link in data:  # data is now an array of links, not objects
        output_file.write(link + '\n')  # Write each link followed by a newline