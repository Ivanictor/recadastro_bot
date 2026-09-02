from fastapi import FastAPI
import uvicorn
from routers.listener import router
from contextlib import asynccontextmanager
from services.request_whatsapp import iniciar_whatsapp

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Iniciando o app e conectando ao serviço do WhatsApp...")

    try:
        iniciar_whatsapp()

    except Exception as e:
        print(f"Não foi possível conectar ao WhatsApp: {e}")

    yield

    print("Encerrando app")

app = FastAPI(lifespan=lifespan)

app.include_router(router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)