# image_api
Simple api for zooming and cropping images


# Setup
This project use python 3.6.

Clone this repo and run `pip install -r requirements.txt`

# Run
`python server.py`

# Usage
For API description ans example of usage project contain Postman collection. 
For more detail go to https://www.getpostman.com/docs/v6/postman/collections/intro_to_collections

If you don't use Postman here are examples for `curl`:
* Upload image: `curl -F 'file=@/Users/admin/Downloads/4.jpg' http://localhost:5000/upload`
* Download image: `curl  -X GET http://127.0.0.1:5000/download/3e3b21bb-169c-4b9c-a6b9-ffcde2f990a9\?zoom\=23\&left\=100\&right\=200\&top\=300\&bottom\=400a`
