import uvicorn

def main():
    uvicorn.run("gitm8.main:app", host="127.0.0.1", port=8000, reload=True)
