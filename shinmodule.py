import csv

def write_to_csv(outputFileName, dataList, header = ""):
    with open(outputFileName, 'w', newline='', encoding='utf-8') as f:
        if (len(header) > 0):
            f.write(f'{header}')

        writer = csv.writer(f)
        for d in dataList:
            writer.writerow(d)
    print(f"Data written to {outputFileName}")

