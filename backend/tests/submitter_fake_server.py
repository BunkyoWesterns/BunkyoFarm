import uvicorn, random
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Tuple

app = FastAPI()

def get_random_status(flag):
    choice = random.randrange(1,50)
    if choice == 45:
        return (flag, 'invalid', "The flag is not valid")
    elif choice == 46:
        return (flag, 'timeout', "Too old")
    elif choice == 47:
        return (flag, 'invalid', "NOP flag")
    return (flag, 'ok', f'points: {random.randrange(1,10)}')

@app.post("/", response_model=List[Tuple[str, str, str]])
async def fake_submit(data: List[str]):
    return [get_random_status(ele) for ele in data]
    

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == '__main__':
    uvicorn.run(
        "submitter_fake_server:app",
        host="0.0.0.0",
        port=5050,
        reload=False,
        access_log=True,
        workers=1
    )