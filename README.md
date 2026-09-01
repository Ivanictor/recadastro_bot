# Recadastro Bot

O projeto foi criado para estabelecer conexão com um bot da SEAD que é utilizado, entre outras funções, para o recadastro dos usuários do órgão. Com a conexão, o programa coleta as informações dos usuários que procedem com o recadastro e as utiliza para localizar o gerente da área e notificá-lo sobre o processo para que o assine.

## Estrutura

O projeto foi construído com a utilização das seguintes tecnologias:

`Python`: Linguagem principal <br>
`FastAPI`: Framework utilizado para a criação da API <br>
`Uvicorn`: Execução da aplicação web em desenvolvimento <br>
`SMTP`: Protocolo para envio do email de aviso <br>
`Baileys.js`: Biblioteca Node.js para conexão com o WhatsApp Web  por meio do protocolo WebSocket. <br>
`RapidFuzz`: Biblioteca Python para realizar correspondência entre o nome digitado e o nome real da unidade usando Fuzzy Matching <br>

## Integrações

- `Dialogflow` — Plataforma responsável pelo chatbot.
- `Webhook` — Mecanismo utilizado pelo Dialogflow para enviar requisições HTTP à API.

## Funcionamento

O Dialogflow divide as seções internas do bot em "Intents". Se a mensagem de entrada do usuário se enquadrar na lista de frases de treinamento, elas são iniciadas e executam as ações programadas em sua lista de ações, salvando as respostas em variáveis. A conexão desse sistema com o fluxo de conversas gerenciado pelo Dialogflow utiliza o "fulfillment", com a ativação de uma webhook em todas as intents que entregam as informações a serem utilizadas. Após a conclusão de uma intent (o usuário preencheu os dados que ela solicitava), todos os dados da intent são enviados como um JSON via webhook. 

Em desenvolvimento, a webhook se conecta à URL fornecida pelo ngrok para se conectar ao endpoint da API (local). 

Para a correta validação dos dados, o programa registra nome e CPF dos usuários e os guarda em uma sessão, identificada pela "session" do Dialogflow. Se o usuário confirmar o envio dos dados na intent seguinte, o programa verifica se as fotos e a confirmação foram enviadas e, em caso afirmativo, utiliza a unidade informada para filtrar o gerente responsável e enviar um email e uma mensagem de aviso no WhatsApp. A filtragem dos gerentes é realizada com a técnica fuzzy matching para realizar a correspondência entre as unidades do banco de dados e a unidade informada. Desse modo, o programa tolera pequenos erros de digitação. Caso o usuário informe um nome inválido para a unidade (correspondência inferior ao limite de tolerância), um email será enviado ao responsável do RH para que tome ciência do processo e o realize manualmente.

Cabe ressaltar que o sistema não foi projetado para analisar o conteúdo das fotos e sim se elas foram enviadas, portanto, a validação dos documentos deve ser feita de forma manual pelos funcionários do órgão.
