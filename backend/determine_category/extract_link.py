import json

# Load the JSON data from the file
with open('output/category_1_recommendations.json', 'r') as file:
    data = json.load(file)

# Open a text file to write the links
with open('output_links.txt', 'w') as output_file:
    for item in data:
        output_file.write(item['link'] + '\n')  # Write each link followed by a newline