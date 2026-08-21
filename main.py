from fastapi import FastAPI
import uvicorn
from routers.submissions import router

app = FastAPI()

app.include_router(router)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)