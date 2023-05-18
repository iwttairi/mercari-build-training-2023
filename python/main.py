import os
import json
import logging
import pathlib
import hashlib
import sqlite3
from fastapi import FastAPI, Form, HTTPException, UploadFile, Depends, File
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()
logger = logging.getLogger("uvicorn")
logger.level = logging.INFO
images = pathlib.Path(__file__).parent.resolve() / "images"
database_path = "../db/mercari.sqlite3"
origins = [ os.environ.get('FRONT_URL', 'http://localhost:3000') ]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET","POST","PUT","DELETE"],
    allow_headers=["*"],
)

# def save_items(name, category, image_filename):
#     with open('items.json', 'r') as f:
#         data = json.load(f)
#     with open("items.json", "w") as f:
#         data["items"].append({"name": name, "category": category, "image_filename": image_filename})
#         json.dump(data, f)

def dict_items(cur, row):
    dictionary = {}
    for idx, col in enumerate(cur.description):
        dictionary[col[0]] = row[idx]
    return dictionary

@app.get("/")
def root():
    return {"message": "Hello, world!"}

@app.post("/items")
def add_item(name: str = Form(...), category: str = Form(...), image: UploadFile = File(...)):
    logger.info(f"Receive item: {name}")
    logger.info(f"Receive item: {category}")
    logger.info(f"Receive item: {image}")
    image = images / image.filename
    try:
        with open(image, "rb") as im:
            image_hash = hashlib.sha256(im.read()).hexdigest()
    except IOError:
        logger.info(f"file doesn't exist")
    image_filename = str(image_hash) + ".jpg"
    con = sqlite3.connect(database_path)
    try:
        with con:
            con.execute("INSERT INTO category (name) VALUES(?)", (category, ))
            con.execute("INSERT INTO items (name, category_id, image_filename) VALUES(?, last_insert_rowid(), ?)", (name, image_filename))
    except sqlite3.Error as e:
        logger.error(f"Error connecting to the database: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    con.close()
    return {"message": f"item received: {name}, {category}, {image}"}

@app.get("/items")
def show_item():
    con = sqlite3.connect(database_path)
    con.row_factory = dict_items
    try:
        with con:
            cur = con.cursor()
            cur.execute("SELECT items.id, items.name, category.name as category, items.image_filename FROM items inner join category on items.category_id = category.id")
            items = {"items": cur.fetchall()}
    except sqlite3.Error as e:
        logger.error(f"Error connecting to the database: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    con.close()
    return items

@app.get("/items/{item_id}")
def item_id(item_id: int):
    try:
        with open("items.json", "r") as f:
            con = json.load(f)
    except IOError:
        logger.info("file doesn't exist")
    items = con.get("items", [])
    if item_id < 1 or item_id > len(items):
        raise HTTPException(status_code=404, detail="Item not found")
    return con["items"][item_id-1]

@app.get("/image/{image_filename}")
async def get_image(image_filename):
    # Create image path
    image = images / image_filename

    if not image_filename.endswith(".jpg"):
        raise HTTPException(status_code=400, detail="Image path does not end with .jpg")

    if not image.exists():
        logger.debug(f"Image not found: {image}")
        image = images / "default.jpg"

    return FileResponse(image)

@app.get("/search")
def search(keyword: str):
    con = sqlite3.connect(database_path)
    con.row_factory = dict_items
    cur = con.cursor()
    match_keyword = '%' + keyword + '%'
    try:
        with con:
            cur = con.cursor()
            cur.execute("SELECT items.id, items.name, category.name AS  category, items.image_filename FROM items inner join category on items.category_id = category.id WHERE items.name LIKE ?", (match_keyword,))
            items = {"items": cur.fetchall()}
    except sqlite3.Error as e:
        logger.error(f"Error connecting to the database: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    con.close()
    return items

