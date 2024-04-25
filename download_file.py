import requests

def download_file(url, filename):
    try:
        # Send a GET request to the URL
        response = requests.get(url)
        
        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Open the file in binary write mode and write the content from the response
            with open(filename, 'wb') as f:
                f.write(response.content)
            print("File downloaded successfully as", filename)
            print(response.headers)
        else:
            print("Failed to download the file. Status code:", response.status_code)
    except Exception as e:
        print("An error occurred:", str(e))

# Example usage:
url = "http://www.ics.uci.edu/~eppstein/pix/vienna/schoenbrunn/Columbary.html"
filename = "sample_file.html"
download_file(url, filename)
