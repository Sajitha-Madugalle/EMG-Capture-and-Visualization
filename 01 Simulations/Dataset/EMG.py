import csv

# Input and output file paths
input_file = "input.txt"
output_file = "output.csv"

# Read and write
with open(input_file, "r") as infile, open(output_file, "w", newline="") as outfile:
    reader = (line.strip().split() for line in infile)  # Split by any whitespace
    writer = csv.writer(outfile)

    for row in reader:
        writer.writerow(row)

print(f"CSV file created successfully: {output_file}")
