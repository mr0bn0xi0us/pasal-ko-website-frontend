from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import requests
from datetime import datetime
import json
import base64

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

PRODUCTS_URL = "https://pasalkowebsite.up.railway.app/products"
REMOTE_API_BASE_URL = "https://pasal-ko-website-production.up.railway.app"


# Function to fetch user data
def fetch_user(user_id, access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(f"{REMOTE_API_BASE_URL}/users/{user_id}", headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return None


def fetch_products(search=None):
    if search:
        response = requests.get(f"{PRODUCTS_URL}?search={search}")
    else:
        response = requests.get(PRODUCTS_URL)

    if response.status_code == 200:
        return response.json()
    else:
        return []


# Helper function to parse JWT token
def parse_jwt(token):
    try:
        base64_url = token.split(".")[1]
        base64_bytes = base64_url.replace("-", "+").replace("_", "/")
        decoded_bytes = base64.b64decode(base64_bytes + "==")
        decoded_str = decoded_bytes.decode("utf-8")
        return json.loads(decoded_str)
    except Exception as e:
        print(f"Error parsing JWT: {e}")
        return {}


@app.get("/user", response_class=HTMLResponse)
async def user_page(request: Request):
    access_token = request.cookies.get("access_token") or request.query_params.get(
        "access_token"
    )
    if not access_token:
        return RedirectResponse(url="/login")

    user_id = parse_jwt(access_token).get("user_id")
    if not user_id:
        return RedirectResponse(url="/login")

    user = fetch_user(user_id, access_token)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return templates.TemplateResponse("user.html", {"request": request, "user": user})


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login", response_class=HTMLResponse)
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    data = {"username": username, "password": password}

    response = requests.post(f"{REMOTE_API_BASE_URL}/login", data=data)

    if response.status_code == 200:
        access_token = response.json().get("access_token")

        # Redirect to the main page after successful login
        response = RedirectResponse(url="/", status_code=303)

        # Set the access token in cookies for subsequent requests
        response.set_cookie(key="access_token", value=access_token)

        return response
    else:
        error_message = "Login failed. Please check your credentials."
        return templates.TemplateResponse("login.html", {"request": request, "error_message": error_message})


@app.exception_handler(404)
async def not_found_exception_handler(request, exc):
    return templates.TemplateResponse(
        "error.html", {"request": request, "error_message": str(exc)}
    )


def format_datetime(value, format="%Y-%m-%dT%H:%M:%S.%fZ"):
    dt = datetime.strptime(value, format)
    return dt.strftime("%B %d, %Y %I:%M %p")


@app.get("/", response_class=HTMLResponse)
async def read_home(request: Request, search: str = None):
    products = fetch_products(search)
    return templates.TemplateResponse(
        "home.html", {"request": request, "products": products}
    )


@app.get("/{product_id}", response_class=HTMLResponse)
async def read_product(product_id: int, request: Request):
    url = f"{PRODUCTS_URL}/{product_id}"
    response = requests.get(url)

    if response.status_code == 200:
        product = response.json()
        return templates.TemplateResponse(
            "product.html", {"request": request, "product": product}
        )
    elif response.status_code == 404:
        error_message = f"Product with id {product_id} not found"
        return templates.TemplateResponse(
            "product_not_found.html",
            {"request": request, "error_message": error_message},
        )
    else:
        error_message = f"Error fetching product details: {response.status_code}"
        return templates.TemplateResponse(
            "error.html", {"request": request, "error_message": error_message}
        )


templates.env.filters["datetimeformat"] = format_datetime
