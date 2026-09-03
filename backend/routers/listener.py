from fastapi import APIRouter
from models.webhook import Webhook

router = APIRouter()

@router.post("/webhook")
def webhook(dados: Webhook):

    print(dados)