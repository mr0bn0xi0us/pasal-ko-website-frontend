from fastapi import FastAPI, Request
from datetime import datetime
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import requests

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

PRODUCTS_URL = "https://pasalkowebsite.up.railway.app/products"


@app.get("/", response_class=HTMLResponse)
async def read_home(request: Request, search: str = None):
    if search:
        response = requests.get(f"{PRODUCTS_URL}?search={search}")
    else:
        response = requests.get(PRODUCTS_URL)

    if response.status_code == 200:
        products = response.json()
    else:
        products = []

    return templates.TemplateResponse(
        "home.html", {"request": request, "products": products}
    )

def datetimeformat(value, format='%Y-%m-%dT%H:%M:%S.%fZ'):
    dt = datetime.strptime(value, format)
    return dt.strftime('%B %d, %Y %I:%M %p')

# Add custom filter to Jinja2 environment
templates.env.filters['datetimeformat'] = datetimeformat

@app.get("/{product_id}", response_class=HTMLResponse)
async def read_product(product_id: int, request: Request):
    try:
        url = f"{PRODUCTS_URL}/{product_id}"
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx, 5xx)
        product = response.json()
        
        if response.status_code == 404:
            error_message = f"Product with id {product_id} not found"
            return templates.TemplateResponse("product_not_found.html", {"request": request, "error_message": error_message})
            
    except requests.exceptions.RequestException as e:
        error_message = f"Error fetching product details: {str(e)}"
        return templates.TemplateResponse("error.html", {"request": request, "error_message": error_message})
    
    return templates.TemplateResponse("product.html", {"request": request, "product": product})