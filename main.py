from fastapi import FastAPI, Form, Request, status
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
from pydantic import BaseModel

from topo_lg import part_4_graph

app = FastAPI()

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Create a class for the input data
class InputData(BaseModel):
 messages: list
 uuidthread: str
 language: str

# Create a class for the output data
class OutputData(BaseModel):
 content: str

def _print_event(event: dict, _printed: set, max_length=1500):
    current_state = event.get("dialog_state")
    # if current_state:
    #     print("Currently in: ", current_state[-1])
    message = event.get("messages")
    if message:
        if isinstance(message, list):
            message = message[-1]
            # print("Currently in: ", message.type, message)
        if message.type == "human":
            return
        if message.id not in _printed:
            _printed.add(message.id)
            return message.content

def gen_answ(ftxt, thread_id, language="en"):
    print("gen_answ", ftxt, thread_id)
    #
    config = {
        "configurable": {
            "thread_id": thread_id,
            "language": language,
        }
    }
    _printed = set()
    # while True:
    events = part_4_graph.stream(
        {"messages": ("user", ftxt)}, config, stream_mode="values", debug=True
    )
    mmess = []
    for event in events:
        mmess.append(_print_event(event, _printed))
    print("out: ", mmess[-1])

    return mmess[-1]

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    print('Request for index page received')
    return templates.TemplateResponse('index.html', {"request": request})

@app.get('/favicon.ico')
async def favicon():
    file_name = 'favicon.ico'
    file_path = './static/' + file_name
    return FileResponse(path=file_path, headers={'mimetype': 'image/vnd.microsoft.icon'})

@app.post('/hello', response_class=HTMLResponse)
async def hello(request: Request, name: str = Form(...)):
    if name:
        print('Request for hello page received with name=%s' % name)
        return templates.TemplateResponse('hello.html', {"request": request, 'name':name})
    else:
        print('Request for hello page received with no name or blank name -- redirecting')
        return RedirectResponse(request.url_for("index"), status_code=status.HTTP_302_FOUND)

# Create a route for the web application
@app.post("/generate")
async def generate(request: Request, input_data: InputData):
    # Get the prompt from the input data
    req = input_data.messages[-1]
    # print('p', req['content'])
    # print('t', input_data.uuidthread)
    # Generate a response from the local LLM using the prompt
    content = gen_answ(req['content'], input_data.uuidthread, input_data.language)
    # Return the response as output data
    return OutputData(content=content)


if __name__ == '__main__':
    uvicorn.run('main:app', host='0.0.0.0', port=8000)

