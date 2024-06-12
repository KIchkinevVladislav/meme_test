import uvicorn
from fastapi import FastAPI

# router here 

app = FastAPI()


# include here



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)